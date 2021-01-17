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

def getToken():
    with open("token.txt", "r") as f:
        return f.read()