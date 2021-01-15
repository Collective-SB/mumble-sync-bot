import discord
from discord.ext import commands
import InterVars as v
import contextlib
import io

class DiscordManager():
    prefix = "#"
    description = "Mumble - Discord sync bot."
    ready = False
    bot = commands.Bot(command_prefix=prefix, description=description)

    def __init__(self):
        self.bot.add_cog(Utilities())

    @bot.event
    async def on_ready():
        await v.botManager.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="code be written"))
        v.botManager.ready = True
        print("Logged in as " + v.botManager.bot.user.name)

class Utilities(commands.Cog):
    """General utilities"""
    @commands.command()
    async def ping(self, ctx):
        await ctx.send("Pong! Latency is " + str(round(v.botManager.bot.latency * 1000)) + "ms")

    @commands.command()
    #FIXME add auth
    async def eval(self, ctx, *, code):
        author = ctx.message.author
        if author.id == 318756837266554881:
            str_obj = io.StringIO() #Retrieves a stream of data
            try:
                with contextlib.redirect_stdout(str_obj):
                    exec(code)
            except Exception as e:
                return await ctx.send(f"```python{e.__class__.__name__}: {e}```")
            await ctx.send(f'```{str_obj.getvalue()}```')
        else:
            image = discord.File("nothingHere.jpg")
            await ctx.send("No u", file=image)

def getToken():
    with open("token.txt", "r") as f:
        return f.read()

def run():
    v.botManager = DiscordManager()
    v.botManager.bot.run(getToken())

run()