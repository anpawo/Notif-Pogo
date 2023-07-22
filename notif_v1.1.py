#!/usr/bin/env python


from getPokemon import *
from ast import literal_eval
from discord import *
from discord.ext import tasks, commands
from time import time
from dotenv import dotenv_values


DEX = literal_eval(open("data/dex.txt").read())
SECRET = dotenv_values('.env')
BOT_TOKEN = SECRET['bot_token']
RARE_CHANNEL = 1127260893332377700


class pogoBot:
    def __init__(self) -> None:
        self.client: Client = self.initClient()
        self.rareChannel = None
        self.pkmQueue: list[Pokemon] = []
        self.tmpMsg: dict[int:int] = {}
        self.newPkm: list[Pokemon] = []
        self.catchList: dict[str:int] = literal_eval(open("data/catch_list.txt").read())
        self.avoidList: dict[str:int] = literal_eval(open("data/avoid_list.txt").read())


    def initClient(self) -> Client:
        intents = Intents.default()
        intents.message_content = True
        return Client(intents=intents)


    def initChannel(self) -> None:
        self.rareChannel = self.client.get_channel(RARE_CHANNEL)


    async def clearChannel(self) -> None:
        nbrMsgFound = 0
        async for msg in self.rareChannel.history():
            nbrMsgFound += 1
            await msg.delete()
        if nbrMsgFound == 100:
            await self.clearChannel()


    async def send(self, msg: str) -> None:
        snowflake = (await self.rareChannel.send(f'```{msg}```')).id
        key = time() + 30
        while self.tmpMsg.__contains__(key):
            key += 1
        self.tmpMsg[key] = snowflake


    async def showList(self, msg: Message) -> None:
        tmpList = self.catchList if msg.content[0] == '?' else self.avoidList
        string = 'avoid' if msg.content[0] == '!' else 'catch'
        string += ' list\n\n'
        for pkm, lvl in tmpList.items():
            string += f'{pkm} {lvl}\n'
        await msg.delete()
        await self.send(string)


    def updateList(self, listName: str) -> None:
        List = eval('self.' + listName + 'List')
        updatedList = {key: List[key] for key in sorted(List.keys())}
        setattr(self, listName + 'List', updatedList)
        with open(f'data/{listName}_list.txt', 'w') as file:
            file.write(str(updatedList))


    async def clearRoomFromPkm(self, name: str) -> None:
        i = 0
        while i < len(self.pkmQueue):
            pkm = self.pkmQueue[i]
            if pkm.name != name:
                i += 1
                continue
            if self.isValidPkm(pkm):
                i += 1
            else:
                msg = await self.rareChannel.fetch_message(pkm.snowflake)
                await msg.delete()
                self.pkmQueue.pop(i)


    async def parseCommand(self, msg: Message) -> None:
        listName = 'catch' if msg.content[0] == '?' else 'avoid'
        List = eval('self.' + listName + 'List')
        args = msg.content[1:].split()
        await msg.delete()
        name = formatName(args[0])
        if name not in DEX:
            await self.send(f'Error: invalid pokemon name: \'{name}\'')
            return
        if len(args) == 1:
            lvl = 0 if listName == 'catch' else 36
        else:
            if args[1].isnumeric():
                lvl = int(args[1])
            else:
                await self.send(f'Error: invalid lvl: {args[1]}')
                return
        if name in List and len(args) == 1:
            del List[name]
        else:
            List[name] = lvl
        await self.clearRoomFromPkm(name)
        self.updateList(listName)


    def isInCatchList(self, pkm: Pokemon) -> bool:
        lvl = self.catchList.get(pkm.name)
        if lvl == None:
            return False
        if lvl > pkm.lvl:
            return False
        return True


    def isInAvoidList(self, pkm: Pokemon) -> bool:
        lvl = self.avoidList.get(pkm.name)
        if lvl == None:
            return False
        if pkm.lvl >= lvl:
            return False
        return True


    def isFullyEvolved(self, pkm: Pokemon) -> bool:
        return 'evos' not in DEX[pkm.name]


    def isValidPkm(self, pkm: Pokemon) -> bool:
        if pkm.iv != 100:
            return False
        if self.isInCatchList(pkm):
            return True
        if self.isInAvoidList(pkm):
            return False
        if self.isFullyEvolved(pkm) or pkm.cp > 1500:
            return True
        return False


    def deleteNonRare(self) -> None:
        i = 0
        while i < len(self.newPkm):
            pkm = self.newPkm[i]
            if self.isValidPkm(pkm):
                i += 1
            else:
                self.newPkm.pop(i)


    async def deleteOutdatedMsg(self) -> None:
        timeAtm = time()
        keysToDel = []
        for key in self.tmpMsg:
            if key < timeAtm:
                msg = await self.rareChannel.fetch_message(self.tmpMsg[key])
                await msg.delete()
                keysToDel.append(key)
        for key in keysToDel:
            self.tmpMsg.__delitem__(key)


    async def deleteOutdatedPkm(self) -> None:
        atmTime = time()
        i = 0
        while i < len(self.pkmQueue):
            if self.pkmQueue[i].dsp < atmTime:
                msg = await self.rareChannel.fetch_message(self.pkmQueue[i].snowflake)
                await msg.delete()
                self.pkmQueue.pop(i)
            else:
                i += 1
        i = 0
        while i < len(self.newPkm):
            if self.newPkm[i].dsp < atmTime:
                self.newPkm.pop(i)
            else:
                i += 1


    def deleteDouble(self) -> None:
        i = 0
        while i < len(self.newPkm):
            pkm = self.newPkm[i]
            if self.pkmQueue.count(pkm) != 0 or self.newPkm.count(pkm) != 1:
                self.newPkm.pop(i)
            else:
                i += 1


    def makeEmbed(self, pkm: Pokemon) -> Embed:
        embed = Embed(
            title = f'{DEX[pkm.name]["name"]} {pkm.size}',
            description = f'**cp** {pkm.cp}\n**lvl** {pkm.lvl}\n**despawn** <t:{pkm.dsp}:R> (<t:{pkm.dsp}:T>)\n[Link]({pkm.id})',
            color = 0xff0000 if (pkm.lvl == 35 or pkm.size != '') else 0x00ff00
        )
        embed.set_thumbnail(url = pkm.thumb)
        return embed


    async def sendNewPkm(self) -> None:
        for pkm in self.newPkm:
            pkm.snowflake = (await self.rareChannel.send(embed = self.makeEmbed(pkm))).id


    async def scrapUpdate(self) -> None:
        await self.deleteOutdatedMsg()
        self.newPkm = getPkmFromAllChannel()
        await self.deleteOutdatedPkm()
        self.deleteDouble()
        self.deleteNonRare()
        await self.sendNewPkm()
        self.pkmQueue += self.newPkm


bot = pogoBot()


@tasks.loop(minutes=1)
async def scrapUpdate():
    await bot.scrapUpdate()


@bot.client.event
async def on_ready() -> None:
    bot.initChannel()
    print(f'{bot.client.user} is now running')
    await bot.clearChannel()
    scrapUpdate.start()


@bot.client.event
async def on_message(msg: Message) -> None:
    if msg.author == bot.client.user or msg.channel.id != RARE_CHANNEL:
        return
    if msg.content[0] not in '!?':
        await bot.send('invalid command')
    elif len(msg.content) == 1 or msg.content[1:].isspace():
        await bot.showList(msg)
    else:
        await bot.parseCommand(msg)

bot.client.run(BOT_TOKEN)
