#!/usr/bin/env python


from __future__ import annotations
from pkm import *
import subprocess


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
    "quickmove",
    "chargedmove",
}


def ruleRespected(rule: dict, pokemon: Pokemon) -> bool:
    if "avoid" in rule:
        return False
    if "iv" not in rule and pokemon.iv != 100:
        return False
    for criteria in rule:
        if criteria == "fe":
            if not isFullyEvolved(pokemon):
                return False
        elif criteria == "size":
            if rule[criteria] == "any":
                if getattr(pokemon, criteria) == "":
                    return False
            elif getattr(pokemon, criteria) != rule[criteria]:
                return False
        elif criteria in ["country", "gender", "quickmove", "chargedmove"]:
            if (
                getattr(pokemon, criteria).replace(" ", "").lower()
                != rule[criteria].replace("", "").lower()
            ):
                return False
        elif criteria in ["iv", "lvl", "cp"]:
            if criteria == "iv" and "/" in rule[criteria]:
                if pokemon.ivs != rule[criteria]:
                    return False
            else:
                value = getattr(pokemon, criteria)
                expected_value = rule[criteria][1]
                operator = rule[criteria][0]
                if operator == "=":
                    if value != expected_value:
                        return False
                elif operator == "<":
                    if value > expected_value:
                        return False
                elif operator == ">":
                    if value < expected_value:
                        return False
    return True


async def applyRules(bot, pokemons: list[Pokemon]) -> None:
    if len(bot.rules) == 0:
        return None
    index = 0
    while index < len(pokemons):
        pokemon = pokemons[index]
        keepPokemon = 0
        if "all" in bot.rules:
            for rule in bot.rules["all"]:
                if ruleRespected(rule=rule, pokemon=pokemon):
                    if "catch" in rule:
                        keepPokemon = 2
                        break
                    else:
                        keepPokemon = 1
        if keepPokemon == 2:
            index += 1
            continue
        if pokemon.name in bot.rules:
            keepPokemon = 0
            if not (
                len(bot.rules[pokemon.name]) == 1
                and "avoid" in bot.rules[pokemon.name][0]
            ):
                for rule in bot.rules[pokemon.name]:
                    if ruleRespected(rule=rule, pokemon=pokemon):
                        keepPokemon = 1
                        break
        if keepPokemon == 0:
            if pokemon.snowflake != None:
                message = await bot.channel.fetch_message(
                    bot.pokemonQueue[index].snowflake
                )
                await message.delete()
            pokemons.pop(index)
        else:
            index += 1


def addCriteria(
    args: list[str], index: int, newRule: dict[str:any], isAllRule: bool
) -> tuple[str, int]:
    if "avoid" in newRule:
        return "the 'avoid' criteria can only be alone in a rule", 0
    criteria = args[index].lower()
    if criteria not in CRITERIAS:
        return makeError("criteria", name=args[index]), 0
    if criteria in newRule:
        return makeError("repetition", name=args[index]), 0
    if criteria in ["avoid", "fe", "catch"]:
        if criteria == "avoid":
            if isAllRule:
                return makeError("avoid"), 0
            if len(newRule) != 0:
                return "the 'avoid' criteria can only be alone in a rule", 0
        if criteria == "catch" and not isAllRule:
            return makeError("catch"), 0
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
        if args[index + 1].lower() not in ["any", "xxs", "xxl"]:
            return makeError("value", name=args[index + 1], value="any, xxs, xxl"), 0
        newRule[criteria] = args[index + 1].lower()
        return "", 2
    elif criteria == "gender":
        if args[index + 1] not in ["male", "female", "genderless"]:
            return makeError("value", name=args[index + 1], value="male, female"), 0
        newRule[criteria] = args[index + 1]
        return "", 2
    else:
        newRule[criteria] = args[index + 1].lower()
        return "", 2


def rewriteRules(bot, pokemonUpdated: str) -> None:
    bot.rules = dict(sorted(bot.rules.items()))
    with open("data/rules.json", "w") as file:
        file.write(json.dumps(bot.rules))
    subprocess.call(["git", "add", "."])
    subprocess.call(["git", "commit", "-m", f"[update] {pokemonUpdated}"])
    subprocess.call(["git", "push"])


async def addRule(args: list[str], bot) -> str:
    pokemonName = formatName(args[0])
    if pokemonName not in DEX and pokemonName != "all":
        return makeError("pkmName", name=args[0])
    isAllRule = pokemonName == "all"
    newRule: dict = {}
    index = 1
    while index < len(args):
        error, indexIncrement = addCriteria(args, index, newRule, isAllRule)
        if error:
            return error
        index += indexIncrement
    if pokemonName not in bot.rules:
        bot.rules[pokemonName] = []
    else:
        for rule in bot.rules[pokemonName]:
            if rule == newRule:
                return ""
    bot.rules[pokemonName].append(newRule)
    rewriteRules(bot, pokemonName)
    await applyRules(bot, bot.pokemonQueue)
    return ""


async def delRule(args: list[str], bot) -> str:
    pokemonName = formatName(args[0])
    if pokemonName not in DEX and pokemonName != "all":
        return makeError("pkmName", name=args[0])
    if pokemonName not in bot.rules:
        return ""
    if len(args) == 1:
        del bot.rules[pokemonName]
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
        if len(bot.rules[pokemonName]) == 0:
            del bot.rules[pokemonName]
    rewriteRules(bot, pokemonName)
    await applyRules(bot, bot.pokemonQueue)
    return ""


def makeMessagePart(bot) -> list[str]:
    maxLength = 1950
    messagePart = []
    currentPart = "\n"
    for pokemon in bot.rules:
        if pokemon == "all":
            continue
        temp = DEX[pokemon]["name"]
        if len(bot.rules[pokemon]) == 1:
            space = " " * (20 - len(temp))
            temp += space + str(bot.rules[pokemon][0]) + "\n"
        else:
            temp += "\n"
            space = " " * 6
            for rule in bot.rules[pokemon]:
                temp += space + str(rule) + "\n"
        if len(currentPart) + len(temp) > maxLength:
            messagePart.append(currentPart)
            currentPart = "\n"
        currentPart += temp
    messagePart.append(currentPart)
    temp = "\nAll\n"
    for rule in bot.rules["all"]:
        temp += " " * 6 + str(rule) + "\n"
    temp += "\n"
    messagePart.append(temp)
    return messagePart


async def showRule(args: list[str], bot) -> str | list[str]:
    pokemonName = "." if len(args) == 0 else formatName(args[0])
    output = ""
    if pokemonName == ".":
        return makeMessagePart(bot)
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


async def helpRule(args: list[str], bot) -> str:
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


ERRORS = {
    "cmdName": "Invalid Command Name: '{name}'",
    "pkmName": "Invalid Pokemon Name: '{name}'",
    "criteria": "Invalid Criteria Name: '{name}'",
    "missing": "Missing Argument '{name}'",
    "value": "Invalid Value '{name}' expected '{value}'",
    "repetition": "Too Many Criteria '{name}'",
    "avoid": "The 'all' rule cannot have the 'avoid' criteria in it.",
    "catch": "The 'catch' criteria can only be in the 'all' rule",
}


def makeError(errorName: str, **customParameter) -> str:
    newError = (
        "Error: " + ERRORS[errorName].format(**customParameter) + "\n'help' for help"
    )
    return newError


COMMANDS = {
    "add": addRule,
    "del": delRule,
    "show": showRule,
    "help": helpRule,
}


async def executeCommand(args: list[str], bot) -> str | list[str]:
    commandName = args[0].lower()
    if len(args) == 1:
        if commandName == "!":
            return await COMMANDS["add"]([bot.findNameNewestPokemon(), "avoid"], bot)
        else:
            return await COMMANDS[commandName](
                [bot.findNameNewestPokemon()] + args, bot
            )
    if commandName not in COMMANDS:
        if commandName[0] == "!" and formatName(commandName) in DEX:
            return await COMMANDS["add"]([formatName(commandName), "avoid"], bot)
        elif commandName == "all" or formatName(commandName) in DEX:
            return await COMMANDS["add"](args, bot)
        else:
            return makeError("cmdName", name=args[0])
    return await COMMANDS[commandName](args[1:], bot)
