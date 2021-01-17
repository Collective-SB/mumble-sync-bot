import discord
from discord.ext import commands
import InterVars as v
import Logger
import contextlib
import io
import asyncio
from threading import *
import MumbleManager
import utilities

prefix = "#"
description = f"A bot to sync Mumble and Discord. Use {prefix}help for help.\nMade by IHave for Collective."
bot = commands.Bot(command_prefix=prefix, description=description)
admins = [318756837266554881]

@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="code be written"))
    v.discordReady = True
    Logger.log("Logged in as " + bot.user.name)

@bot.event
async def on_message(message):
    #message sync
    if message.channel.id == 799300636889186304 and message.author.id != bot.user.id:
        name = message.author.name
        content = utilities.stripMarkdown(message.content)

        toSend = f"<b>{name}</b> in Discord: {content}"

        print(str(toSend))
        v.mumble.channels[0].send_text_message(toSend)

    elif f'<@!{bot.user.id}>' in message.content:
        await message.channel.send(f"My prefix is ``{prefix}``! Use ``{prefix}help`` to get a list of commands.")    
    
    #elif "aHR0cHM6Ly9iaXQubHk" in message.content:
    #    await message.channel.send("That looks like a token for authenticating with Mumble! That shouldn't be shared in public channels unless you 100% know what you're doing. It should only be shared with this bot in direct messages. Check the message that contained the token for information about what to do if you accidentally leak it.")
    #    Logger.warn("<@318756837266554881> Possible token exposure at " + str(message))
    else:
        await bot.process_commands(message)

@bot.command()
async def ping(ctx):
    await ctx.send("Pong! Latency is " + str(round(bot.latency * 1000)) + "ms")

@bot.command()
async def eval(ctx, *, code):
    author = ctx.message.author
    if author.id in admins:
        str_obj = io.StringIO() #Retrieves a stream of data
        try:
            with contextlib.redirect_stdout(str_obj):
                exec(code)
        except Exception as e:
            return await ctx.send(f"```python{e.__class__.__name__}: {e}```")
        await ctx.send(f'```{str_obj.getvalue()}```')

@bot.command()
async def about(ctx):
    await ctx.send(f"You might be thinking of the ``{prefix}help`` command.")

@bot.command()
async def online(ctx):
    online = v.mumble.users.count() -1
    if online == 0:
        await ctx.send("There are currently no users on the Mumble server.")

    elif online == 1:
        await ctx.send("There is currently 1 user on the Mumble server.")

    elif utilities.isPow2(online):
        await ctx.send(f"There is currently a nice, round number of people online - {str(online)}")

    else:
        await ctx.send(f"There are currently {str(online)} users on the Mumble server.")

@bot.command()
async def answer(ctx):
    await ctx.send("42")

def getToken():
    with open("token.txt", "r") as f:
        return f.read()