#!/usr/bin/env python


from __future__ import annotations
from pkm import *


ERRORS = {
    "cmdName": "Invalid Command Name '{name}'",
    "pkmName": "Invalid Pokemon Name '{name}'",
    "criteria": "Invalid Criteria Name '{name}'",
    "missing": "Missing Argument '{name}'",
    "value": "Invalid Value '{name}' expected '{value}'",
    "repetition": "Too Many Criteria '{name}'",
}


CRITERIAS = {
    "avoid",
    "catch",
    "fe",
    "lvl",
    "iv",
    "cp",
    "size",
    "country",
    "gender",
}


def ruleRespected(rule: dict, pokemon: Pokemon, forAllRule: bool) -> int:
    keepPokemon = 1
    for criteria in rule:
        if criteria == "fe":
            if not isFullyEvolved(pokemon):
                keepPokemon = 0
        elif criteria in ["size", "country", "gender"]:
            if getattr(pokemon, criteria) != rule[criteria]:  # here
                keepPokemon = 0
        elif criteria in ["iv", "lvl", "cp"]:
            if criteria == "iv" and "/" in rule[criteria]:
                if pokemon.ivs != rule[criteria]:
                    keepPokemon = 0
            else:
                value = getattr(pokemon, criteria)
                expected_value = rule[criteria][1]
                operator = rule[criteria][0]
                if operator == "=":
                    if value != expected_value:
                        keepPokemon = 0
                elif operator == "<":
                    if value > expected_value:
                        keepPokemon = 0
                elif operator == ">":
                    if value < expected_value:
                        keepPokemon = 0
    if "avoid" in rule and len(rule) == 1:
        return -1
    if (
        "avoid" not in rule
        and keepPokemon == 0
        and "catch" not in rule
        and not forAllRule
    ):
        return -1
    if "catch" in rule and keepPokemon == 1:
        return 2
    return keepPokemon


async def applyRules(bot, pokemons: list[Pokemon]) -> None:
    if len(bot.rules) == 0:
        return None
    index = 0
    while index < len(pokemons):
        pokemon = pokemons[index]
        keepPokemon = 0
        for name in ["all", pokemon.name]:
            if name in bot.rules:
                for rule in bot.rules[name]:
                    result = ruleRespected(rule, pokemon, name == "all")
                    if "iv" not in rule and pokemon.iv != 100:
                        result = 0
                    if keepPokemon == -1 and result != 2:
                        continue
                    else:
                        if result == -1:
                            keepPokemon = -1
                        if result == 1:
                            keepPokemon = 1
                        if result == 2:
                            keepPokemon = 2
                            break
            if keepPokemon == 2:
                break
        if keepPokemon < 1:
            if pokemon.snowflake != None:
                message = await bot.channel.fetch_message(
                    bot.pokemonQueue[index].snowflake
                )
                await message.delete()
            pokemons.pop(index)
        else:
            index += 1


def addCriteria(args: list[str], index: int, newRule: dict[str:any]) -> tuple[str, int]:
    criteria = args[index].lower()
    if criteria not in CRITERIAS:
        return makeError("criteria", name=args[index]), 0
    if criteria in newRule:
        return makeError("repetition", name=args[index]), 0
    if criteria in ["avoid", "fe", "catch"]:
        newRule[criteria] = True
        return "", 1
    elif criteria in ["lvl", "iv", "cp"]:
        if criteria == "iv" and "/" in args[index + 1]:
            newRule[criteria] = args[index + 1]
            return "", 2
        if args[index + 1] not in ["<", ">", "="]:
            return makeError("value", name=args[index + 1], value="<, >, ="), 0
        symbol = args[index + 1]
        if not args[index + 2].isdigit():
            return makeError("value", name=args[index + 2], value="integer"), 0
        value = int(args[index + 2])
        newRule[criteria] = [symbol, value]
        return "", 3
    elif criteria == "size":
        if args[index + 1].lower() not in ["xxs", "xxl"]:
            return makeError("value", name=args[index + 1], value="xxs, xxl"), 0
        newRule[criteria] = args[index + 1].lower()
        return "", 2
    elif criteria == "country":
        newRule[criteria] = args[index + 1]
        return "", 2
    elif criteria == "gender":
        if args[index + 1] not in ["male, female", "genderless"]:
            return makeError("value", name=args[index + 1], value="male, female"), 0
        newRule[criteria] = args[index + 1]
        return "", 2


def rewriteRules(bot) -> None:
    with open("data/rules.json", "w") as file:
        file.write(json.dumps(bot.rules))


async def addCommand(args: list[str], bot) -> str:
    pokemonName = formatName(args[0])
    if pokemonName not in DEX and pokemonName != "all":
        return makeError("pkmName", name=args[0])
    newRule: dict = {}
    index = 1
    while index < len(args):
        error, indexIncrement = addCriteria(args, index, newRule)
        if error:
            return error
        index += indexIncrement
    if pokemonName not in bot.rules:
        bot.rules[pokemonName] = []
    if "avoid" in newRule and len(newRule) > 1:
        newRule["avoid"] = False
    bot.rules[pokemonName].append(newRule)
    rewriteRules(bot)
    await applyRules(bot, bot.pokemonQueue)
    return f"{pokemonName} {bot.rules[pokemonName]}"


async def delCommand(args: list[str], bot) -> str:
    pokemonName = formatName(args[0])
    if pokemonName not in DEX and pokemonName != "all":
        return makeError("pkmName", name=args[0])
    if len(args) == 1:
        bot.rules[pokemonName].clear()
    else:
        try:
            index = int(args[1])
        except IndexError:
            return makeError("missing", name="indexDeletion")
        except ValueError:
            return makeError("value", name=args[1], value="integer")
        if len(bot.rules[pokemonName]) <= index:
            return makeError(
                "value", name=index, value=f"0-{len(bot.rules[pokemonName]) - 1}"
            )
        del bot.rules[pokemonName][index]
    rewriteRules(bot)
    await applyRules(bot, bot.pokemonQueue)
    return ""


async def showCommand(args: list[str], bot) -> str:
    pokemonName = "." if len(args) == 0 else formatName(args[0])
    output = ""
    if pokemonName == ".":
        for pkm in bot.rules:
            if pkm == "all":
                continue
            else:
                output += f"{DEX[pkm]['name']}:\n"
            for rule in bot.rules[pkm]:
                output += f"\t{rule}\n"
        output += f"all:\n"
        for rule in bot.rules["all"]:
            output += f"\t{rule}\n"
        if output == "":
            return "No rules made any pokemon"
    elif pokemonName == "all":
        if "all" not in bot.rules:
            return f"No rules for 'all'"
        output += f"all:\n"
        for rule in bot.rules[pokemonName]:
            output += f"\t{rule}\n"
    elif pokemonName in DEX:
        if pokemonName not in bot.rules:
            return f"No rules for '{pokemonName}'"
        output += f"{DEX[pokemonName]['name']}:\n"
        for rule in bot.rules[pokemonName]:
            output += f"\t{rule}\n"
    else:
        return makeError("pkmName", name=args[0])
    return output


async def helpCommand(args: list[str], bot) -> str:
    if len(args) == 0:
        output = "⏤" * 50 + "\n\n"
        for cmd in COMMANDS:
            output += open(f"help/{cmd}.txt").read() + "\n"
            output += "⏤" * 50 + "\n\n"
        return output
    else:
        commandName = args[0].lower()
        if commandName not in COMMANDS:
            return makeError("cmdName", name=args[0])
        return open(f"help/{commandName}.txt").read()


def makeError(errorName: str, **customParameter) -> str:
    newError = (
        "Error: " + ERRORS[errorName].format(**customParameter) + "\n'help' for help"
    )
    return newError


COMMANDS = {
    "add": addCommand,
    "del": delCommand,
    "show": showCommand,
    "help": helpCommand,
}


async def executeCommand(args: list[str], bot) -> str:
    commandName = args[0].lower()
    if commandName not in COMMANDS:
        if commandName[0] == "!" and formatName(commandName) in DEX:
            return await COMMANDS["add"]([formatName(commandName), "avoid"], bot)
        elif commandName == "all" or formatName(commandName) in DEX:
            return await COMMANDS["add"](args, bot)
        else:
            return makeError("cmdName", name=args[0])
    return await COMMANDS[commandName](args[1:], bot)
