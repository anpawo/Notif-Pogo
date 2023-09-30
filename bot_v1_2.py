#!/usr/bin/env python

from __future__ import annotations
from my_request import *
from my_command import *
from dotenv import dotenv_values
from discord import *
from discord.ext import tasks
from time import time


BOT_TOKEN = SECRETS["bot_token"]
CHANNEL_ID = 1127260893332377700


def initClient() -> Client:
    intents = Intents.default()
    intents.message_content = True
    return Client(intents=intents)


def makeEmbed(pkm: Pokemon) -> Embed:
    gender_icon = {
        "male": "<:male:1134911469545341009>",
        "female": "<:female:1134911466156339310>",
        "genderless": "<:genderless:1134911468123472024>",
    }
    embed = Embed(
        title=f"{DEX[pkm.name]['name']} {gender_icon[pkm.gender]} {pkm.size.upper()}",
        description=f"**cp** {pkm.cp}\n**lvl** {pkm.lvl}\n**ivs** {pkm.ivs}\n**move** {pkm.quickmove} / {pkm.chargedmove}\n**Country** {pkm.country}\n**Despawn** <t:{pkm.despawn}:R> (<t:{pkm.despawn}:T>)\n**[Link]({pkm.urlMessage})**",
        color=(0xFF0000 if (pkm.lvl == 35) else 0x00FF00),
    )
    embed.set_thumbnail(url=pkm.thumb)
    return embed


def splitMessage(message: str) -> list[str]:
    maxLength = 1950
    messageParts = []
    if len(message) < maxLength:
        messageParts.append(message)
    else:
        for i in range(0, len(message), maxLength):
            messageParts.append(message[i : i + maxLength])
    return messageParts


class pogoBot:
    def __init__(self) -> None:
        self.client = initClient()
        self.channel = None
        self.pokemonQueue: list[Pokemon] = []
        self.messageToDelete: dict[int:int] = {}  # id / dsp date
        self.rules: dict[str : list[dict]] = json.load(open("data/rules.json"))
        self.rulesChanged = False

    def startChannel(self) -> None:
        self.channel = self.client.get_channel(CHANNEL_ID)

    async def clearChannel(self) -> None:
        messageCounter = 0
        async for message in self.channel.history():
            messageCounter += 1
            await message.delete()
        if messageCounter == 100:
            await self.clearChannel()

    async def send(self, message: str | list[str]):
        if isinstance(message, str):
            if message == "":
                return None
            messageParts = [message]
        else:
            messageParts = message
        expire = time() + 40
        for part in messageParts:
            messageId = (await self.channel.send(f"```{part}```")).id
            self.messageToDelete[messageId] = expire

    async def deleteOutdatedMessage(self) -> None:
        timeNow = time()
        keysToDelete = []
        for messageId in list(self.messageToDelete.keys()):
            if self.messageToDelete[messageId] < timeNow:
                message = await self.channel.fetch_message(messageId)
                await message.delete()
                keysToDelete.append(messageId)
        for key in keysToDelete:
            self.messageToDelete.__delitem__(key)

    async def deleteOutdatedPokemon(self) -> None:
        timeNow = time()
        index = 0
        while index < len(self.pokemonQueue):
            if self.pokemonQueue[index].despawn < timeNow:
                try:
                    message = await self.channel.fetch_message(
                        self.pokemonQueue[index].snowflake
                    )
                    await message.delete()
                except:
                    print(message.content, self.pokemonQueue[index])
                self.pokemonQueue.pop(index)
            else:
                index += 1

    def deleteDouble(self, newPokemon: list[Pokemon]) -> None:
        index = 0
        while index < len(newPokemon):
            if (
                self.pokemonQueue.count(newPokemon[index]) != 0
                or newPokemon.count(newPokemon[index]) != 1
            ):
                newPokemon.pop(index)
            else:
                index += 1

    async def sendNewPokemon(self, newPokemon: list[Pokemon]) -> None:
        for pokemon in newPokemon:
            pokemon.snowflake = (await self.channel.send(embed=makeEmbed(pokemon))).id

    def findNameNewestPokemon(self) -> str:
        if len(self.pokemonQueue) == 0:
            return "error"
        return self.pokemonQueue[-1].name

    async def update(self) -> None:
        newPokemon = getPkmFromAllChannel()
        self.deleteDouble(newPokemon)
        await applyRules(self, newPokemon)
        await self.sendNewPokemon(newPokemon)
        self.pokemonQueue += newPokemon


bot = pogoBot()


@tasks.loop(minutes=1)
async def scrapUpdate():
    await bot.deleteOutdatedPokemon()
    await bot.deleteOutdatedMessage()
    await bot.update()


@tasks.loop(minutes=60)
async def updateGithub():
    if bot.rulesChanged:
        subprocess.call(["git", "add", "."])
        subprocess.call(["git", "commit", "-m", f"[update rules]"])
        subprocess.call(["git", "push"])
        bot.rulesChanged = False


@bot.client.event
async def on_ready() -> None:
    bot.startChannel()
    print(f"{bot.client.user} is now running")
    await bot.clearChannel()
    scrapUpdate.start()


@bot.client.event
async def on_message(message: Message) -> None:
    if message.author == bot.client.user or message.channel.id != CHANNEL_ID:
        return None
    bot.messageToDelete[message.id] = time() + 30
    output = await executeCommand(message.content.split(), bot)
    await bot.send(output)


bot.client.run(BOT_TOKEN)
