import discord
from discord.ext import commands
import InterVars as v
import contextlib
import io
import Logger

class DiscordManager():
    prefix = "#"
    description = "desc"#f"A bot to sync Mumble and Discord. Use {prefix}help for help.\nMade by IHave for Collective."
    ready = False
    bot = commands.Bot(command_prefix=prefix, description=description)

    admins = [318756837266554881]

    def __init__(self):
        Logger.log("Adding cogs")
        self.bot.add_cog(Utilities())
        Logger.log("Cogs added")

    @bot.event
    async def on_ready():
        await v.botManager.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="code be written"))
        v.botManager.ready = True
        Logger.log("Logged in as " + v.botManager.bot.user.name)

        # bad practice but eh
        await Logger.pushLogLoop()

    @bot.command()
    async def about(ctx):
        await ctx.send("I EXIST")

class Utilities(commands.Cog):
    """General utilities"""
    @commands.command()
    async def ping(self, ctx):
        Logger.log("Running ping")
        await ctx.send("Pong! Latency is " + str(round(v.botManager.bot.latency * 1000)) + "ms")

    @commands.command()
    async def eval(self, ctx, *, code):
        author = ctx.message.author
        if author.id in v.botManager.admins:
            str_obj = io.StringIO() #Retrieves a stream of data
            try:
                with contextlib.redirect_stdout(str_obj):
                    exec(code)
            except Exception as e:
                return await ctx.send(f"```python{e.__class__.__name__}: {e}```")
            await ctx.send(f'```{str_obj.getvalue()}```')
        else:
            Logger.warn("Unauthorised eval attempt by " + str(ctx.message.author.id))
            image = discord.File("nothingHere.jpg")
            await ctx.send("No u", file=image)

def getToken():
    with open("token.txt", "r") as f:
        return f.read()

def run():
    v.botManager = DiscordManager()
    v.botManager.bot.run(getToken())