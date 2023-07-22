#!/usr/bin/env python3


from ast import literal_eval


DEX = literal_eval(open("data/dex.txt").read())


class Pokemon:
    def __init__(self, **kwargs) -> None:
        self.name = kwargs.get('name')
        self.iv = kwargs.get('iv')
        self.lvl = kwargs.get('lvl')
        self.cp = kwargs.get('cp')
        self.dsp = kwargs.get('dsp')
        self.thumb = kwargs.get('thumb')
        self.id = kwargs.get('id')
        self.size = kwargs.get('size')
        self.snowflake = 0


    def __eq__(self, other) -> bool:
        if isinstance(other, Pokemon):
            for attr in vars(self):
                if attr in ['id', 'snowflake']:
                    continue
                if getattr(self, attr) != getattr(other, attr):
                    return False
            return True
        return False


    def __str__(self) -> str:
        string = ''
        for attr in vars(self):
            string += f'{attr} = {getattr(self, attr)}\n'
        return string


    def __repr__(self) -> str:
        return str(self)


def formatName(name: str) -> str:
    i = 0
    while i < len(name):
        if name[i].isalnum() == False:
            name = name[:i] + name[i + 1:]
        else:
            i += 1
    return name.lower()


def deleteSides(string: str, sep: str) -> str:
    while string[0] != sep:
        string = string[1:]
    while string[-1] != sep:
        string = string[:-1]
    return string


def getPkmFromMsg(msg: dict) -> Pokemon:
    try:
        embed = msg['embeds'][0]
    except:
        print('Error:\n', str(msg))
        return None
    value = embed['fields'][0]['value'].split()

    name = formatName(deleteSides(embed['fields'][0]['name'], '*'))
    if name not in DEX:
        name = formatName(deleteSides(embed['fields'][0]['name'], '*').split()[0])
    id = f"https://discord.com/channels/864766766932426772/{msg['channel_id']}/{msg['id']}"
    tmp = embed['fields'][0]['name']
    size = 'XXS' if 'XXS' in tmp else 'XXL' if 'XXL' in tmp else ''
    iv = 0 if value[1] == '?' else int(float(value[1]))
    lvl = int(value[5])
    cp = int(value[8])
    dsp = int(value[value.index('Despawns') + 1][4:-4])
    thumb = embed['thumbnail']['url']
    return Pokemon(name=name, iv=iv, lvl=lvl, cp=cp, dsp=dsp, thumb=thumb, size=size, id=id)


if __name__ == '__main__':
    pkm = Pokemon(name="Pikachu")
    print(pkm)
    name = "_POrygon_2_"
    print(formatName(name))
