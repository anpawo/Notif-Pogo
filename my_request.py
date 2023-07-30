#!/usr/bin/env python


from __future__ import annotations
from dotenv import dotenv_values
from message_parsing import *
import requests
import json
import time


CHANNEL: dict = json.load(open("data/channel.json"))
SECRETS: dict = dotenv_values(".env")
HEADERS: dict = {"authorization": SECRETS["api_authorization"]}


def getPkmFromAllChannel() -> list[Pokemon]:
    timeNow = time.time()
    pokemons = []
    for i in CHANNEL:
        newPokemons = getPkmFromChannel(i)
        index = 0
        while index < len(newPokemons):
            if newPokemons[index].despawn < timeNow:
                newPokemons.pop(index)
            else:
                index += 1
        pokemons += newPokemons
    return pokemons


def getPkmFromChannel(channelName: str) -> list[Pokemon]:
    url = f"https://discord.com/api/v9/channels/{CHANNEL[channelName]}/messages?limit=8"
    response = requests.get(url, headers=HEADERS)
    try:
        messages = json.loads(response.text)
    except json.decoder.JSONDecodeError:
        print(f"Error with channel '{channelName}', id: {CHANNEL[channelName]}")
        return []
    return list(filter(None, map(parseMessage, messages)))


if __name__ == "__main__":
    pokemons = getPkmFromAllChannel()
    for pkm in pokemons:
        print(pkm)
