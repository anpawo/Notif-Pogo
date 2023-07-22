#!/usr/bin/env python3


from __future__ import annotations
from pkmClass import *
from ast import literal_eval
import requests
import json
from dotenv import dotenv_values


CHANNEL: dict = literal_eval(open("data/channel.txt").read())
SECRET: dict = dotenv_values('.env')
AUTHORIZATION: str = SECRET['authorization']


def getMsg(name: str, id: str) -> list:
    url = f"https://discord.com/api/v9/channels/{id}/messages?limit=8"
    headers = {'authorization': AUTHORIZATION}
    response = requests.get(url, headers=headers)
    try:
        msg = json.loads(response.text)
    except json.decoder.JSONDecodeError:
        print(f'Error with channel \'{name}\', id: {id}')
        return []
    return msg



def getPkmFromOneChannel(name: str, id: str) -> list[Pokemon]:
    msg = getMsg(name, id)
    pokemons = []
    for m in msg:
        pkm = getPkmFromMsg(m)
        if pkm != None:
            pokemons.append(pkm)
    return pokemons


def getPkmFromAllChannel() -> list[Pokemon]:
    pokemons = []
    for name, id in CHANNEL.items():
        pokemons += getPkmFromOneChannel(name, id)
    return pokemons


if __name__ == '__main__':
    url = f"https://discord.com/api/v9/channels/1073124987088687114/messages?limit=8"
    headers = {'authorization': AUTHORIZATION}
    response = requests.get(url, headers=headers)
    msg = json.loads(response.text)
    print(msg)