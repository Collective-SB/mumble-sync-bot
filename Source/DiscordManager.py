import discord
from discord.ext import commands
import Database as db
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
        await message.channel.send(embed=makeFancyEmbed("Ping Detected!", f"My prefix is ``{prefix}``! Use ``{prefix}help`` to get a list of commands."))
    
    #elif "aHR0cHM6Ly9iaXQubHk" in message.content:
    #    await message.channel.send("That looks like a token for authenticating with Mumble! That shouldn't be shared in public channels unless you 100% know what you're doing. It should only be shared with this bot in direct messages. Check the message that contained the token for information about what to do if you accidentally leak it.")
    #    Logger.warn("<@318756837266554881> Possible token exposure at " + str(message))
    else:
        await bot.process_commands(message)

@bot.command()
async def ping(ctx):
    await ctx.send(embed=makeFancyEmbed("Ping!", "Pong! Latency is " + str(round(bot.latency * 1000)) + "ms"))

@bot.command()
async def eval(ctx, *, code):
    author = ctx.message.author
    if author.id in admins:
        str_obj = io.StringIO() #Retrieves a stream of data
        try:
            with contextlib.redirect_stdout(str_obj):
                exec(code)
        except Exception as e:
            return await ctx.send(f"python{e.__class__.__name__}: {e}")
        await ctx.send(f'{str_obj.getvalue()}')

@bot.command()
async def about(ctx):
    await ctx.send(embed=makeFancyEmbed("About", f"You might be thinking of the ``{prefix}help`` command."))

@bot.command()
async def online(ctx):
    online = v.mumble.users.count() -1
    if online == 0:
        await ctx.send(embed=makeFancyEmbed("User Count", "There are currently no users on the Mumble server."))

    elif online == 1:
        await ctx.send(embed=makeFancyEmbed("User Count", "There is currently 1 user on the Mumble server."))

    elif utilities.isPow2(online):
        await ctx.send(embed=makeFancyEmbed("User Count", f"There is currently a nice, round number of people online - {str(online)}"))

    else:
        await ctx.send(embed=makeFancyEmbed("User Count", f"There are currently {str(online)} users on the Mumble server."))

@bot.command()
async def answer(ctx):
    await ctx.send(embed=makeFancyEmbed("The Answer to Life, the Universe, and Everything:", "42"))

@bot.command()
async def setAuthorised(ctx, member : discord.Member, allowed : bool):
    _id = member.id
    
    await ctx.send(embed=makeFancyEmbed("Warning", "This is an unsafe command for admin use. Use with care."))
    if allowed == None:
        await ctx.send(embed=makeFancyEmbed("Error", "Allowed variable does not exist or is not able to be converted to type boolean"))

    if ctx.message.author.id in admins:
        query = {"discordID" : _id}
        values = {"$set" : {"discordID" : _id, "allowed" : allowed}}
        db.authorised.update_one(query, values, upsert=True)

        await ctx.send(embed=makeFancyEmbed("Update permissions", "On query " + str(query) + " setting values " + str(values)))

@bot.command()
async def listAllowedRoles(ctx):
    if not checkIfAuthorised(ctx):
        return
    await ctx.send(embed=makeAuthedRolesEmbed())

@bot.command()
async def addAllowedRole(ctx, _id : int):
    if not checkIfAuthorised(ctx):
        return
    toInsert = {"$set" : {"discordID" : _id, "assigner" : ctx.message.author.id}}
    query = {"discordID" : _id}

    db.allowedRoles.update_one(query, toInsert, upsert=True)
    await ctx.send(embed=makeFancyEmbed("Inserted", str(toInsert)))
    await ctx.send(embed=makeAuthedRolesEmbed())

@bot.command()
async def removeAllowedRole(ctx, _id : int):
    if not checkIfAuthorised(ctx):
        return
    query = {"discordID" : _id}

    deletion = db.allowedRoles.delete_many(query)

    if deletion.deleted_count == 0:
        await ctx.send(embed=makeFancyEmbed("Failure", "No records deleted."))
        return

    await ctx.send(embed=makeFancyEmbed("Success", f"Deleted {str(deletion.deleted_count)} documents"))
    await ctx.send(embed=makeAuthedRolesEmbed())

def getToken():
    with open("token.txt", "r") as f:
        return f.read()

def makeAuthedRolesEmbed():
    embed = discord.Embed(title="Authorised Roles", color=0xce0000)

    for role in db.allowedRoles.find():
        embed.add_field(name="Role", value=f"<@&{role.get('discordID')}>")

    embed.set_footer(text="Discord Link by IHave")

    return embed

def makeFancyEmbed(title, text="nothing here"):
    embed = discord.Embed(title=title, description=text, color=0xce0000)
    embed.set_footer(text="Discord Link by IHave")
    return embed

def checkIfAuthorised(ctx):
    _id = ctx.message.author.id

    query = {"discordID" : _id}
    r = db.authorised.find_one(query)

    if r == None:
        return False

    if r["allowed"] == True:
        return True

    return False