#!/usr/bin/env python


from __future__ import annotations
import json


DEX: dict = json.load(open("data/dex.json"))


class Pokemon:
    def __init__(self) -> None:
        self.name: str
        self.gender = "male"
        self.urlMessage: str
        self.size = ""
        self.ivs: str
        self.iv: int
        self.lvl: int
        self.cp: int
        self.despawn: int
        self.thumbnail: str
        self.country: str
        self.snowflake = None

    def __str__(self) -> str:
        string = ""
        for attr in vars(self):
            string += f"{attr} = {getattr(self, attr)}\n"
        return string

    def __repr__(self) -> str:
        return str(self)

    def __eq__(self, other) -> bool:
        if isinstance(other, Pokemon):
            for attr in vars(self):
                if attr in ["urlMessage", "snowflake"]:
                    continue
                if getattr(self, attr) != getattr(other, attr):
                    return False
            return True
        return False


def isFullyEvolved(pkm: Pokemon) -> bool:
    return "evos" not in DEX[pkm.name]


def formatName(name: str) -> str:
    i = 0
    while i < len(name):
        if not name[i].isalnum():
            name = name[:i] + name[i + 1 :]
        else:
            i += 1
    return name.lower()
