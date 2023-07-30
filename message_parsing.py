#!/usr/bin/env python

from __future__ import annotations
from pkm import *
import json


def deleteSides(string: str, sep: str) -> str:
    while string[0] != sep:
        string = string[1:]
    while string[-1] != sep:
        string = string[:-1]
    return string


def parseMessage(msg: dict) -> Pokemon:
    if len(msg["embeds"]) == 0:
        return None
    embed = msg["embeds"][0]
    value = embed["fields"][0]["value"].split()
    pkm = Pokemon()
    for gender in ["female", "male", "genderless"]:
        if gender in embed["fields"][0]["name"]:
            pkm.gender = gender
            break
    pkm.name = formatName(deleteSides(embed["fields"][0]["name"], "*"))
    if pkm.name not in DEX:
        pkm.name = formatName(deleteSides(embed["fields"][0]["name"], "*").split()[0])
    pkm.urlMessage = f"https://discord.com/channels/864766766932426772/{msg['channel_id']}/{msg['id']}"
    for size in ["XXS", "XXL"]:
        if size in embed["fields"][0]["name"]:
            pkm.size = size.lower()
            break
    pkm.ivs = value[2][1:-1]
    pkm.iv = 0 if value[1] == "?" else round(float(value[1]))
    pkm.lvl = int(value[5])
    pkm.cp = int(value[8])
    pkm.despawn = int(value[value.index("Despawns") + 1][4:-4])
    pkm.thumb = embed["thumbnail"]["url"]
    pkm.country = formatName(embed["fields"][0]["value"].split("*")[-7])
    return pkm


if __name__ == "__main__":
    with open("example/message.json", encoding="utf-8") as file:
        msg = json.load(file)
    pkm = parseMessage(msg)
    print(pkm)
