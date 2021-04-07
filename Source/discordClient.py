from discord import client, Game
from discord.ext import commands
from secrets import token_urlsafe
import base64
import shared
import contextlib
import io
import time

ownerID = 318756837266554881

def holds(permName):
    def predicate(ctx):
        if shared.v.app:
            return shared.v.app.db.permissions.count({"name" : permName, "holders" : ctx.author.id}) > 0
        else:
            return False

    return commands.check(predicate)

def createToken():
    #Base64'd Rickroll.
    easterEgg = "https://bit.ly/3ksSjAl"
    token = token_urlsafe(64)

    return base64.b64encode(bytes(easterEgg + " " + token, "ascii")).decode("ascii")

def diffify(intext):
    if len(intext) == 0:
        return ""

    text = f"```diff\n"
    for i in intext.split("\n"):
        if i != "\n" and i != "" and i != " ":
            text += f"- {i} - \n"

    return text + "```"

#I fucking hate this but the docs literally all run by this.
client = commands.Bot(command_prefix="#")

@client.event
async def on_ready():
    print(f"Logged on as {client.user}")
    client.add_cog(Utility(client))
    client.add_cog(AccountLinking(client))
    client.add_cog(Permissions(client))

class Utility(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command()
    async def answer(self, ctx):
        await ctx.send(diffify("42"))

    @commands.command()
    @holds("admin")
    async def evaluate(self, ctx, *, code):
        str_obj = io.StringIO() #Retrieves a stream of data
        try:
            with contextlib.redirect_stdout(str_obj):
                exec(code)
        except Exception as e:
            return await ctx.send(f"python{e.__class__.__name__}: {e}")
        await ctx.send(f'{str_obj.getvalue()}')

class AccountLinking(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command()
    async def linkAccount(self, ctx):
        token = createToken()
        shared.v.app.db.tokens.insert_one({"text" : token, "uid" : ctx.author.id, "created" : time.time()})
        await ctx.send(diffify("PMed you instructions."))
        await ctx.message.author.send(f"""
Here is your token. DM it to the Mumble bot:
```
{token}
```

Keep it safe and **do not share it.**
""")

class Permissions(commands.Cog):
    def __init__(self, client):
        self.client = client

    def has_perm(self, uid, name):
        return shared.v.app.db.permissions.count({"name" : name, "holders" : uid}) > 0
    
    #TODO restrict these cmds
    @commands.command()
    async def listUserPerms(self, ctx, user : commands.MemberConverter):
        perms = shared.v.app.db.permissions.find({"holders" : user.id})
        text = ""
        for perm in perms:
            text += perm["name"] + "\n"

        if text == "":
            text = "No Permissions"

        await ctx.send(diffify(text))

    @commands.command()
    async def listAllPerms(self, ctx):
        perms = shared.v.app.db.permissions.find({})

        text = ""
        for perm in perms:
            text += perm["name"] + "\n"

        await ctx.send(diffify(text))

    #TODO grant, revoke, init
    @commands.command()
    async def grantPerms(self, ctx, member : commands.MemberConverter, permName : str):
        if not permName in shared.v.app.perms:
            await ctx.send(diffify("Permission invalid"))
            return

        if self.has_perm(member.id, permName):
            await ctx.send(diffify("User already holds that permission"))
            return

        query = {"name" : permName}
        new = {"$push" : {"holders" : member.id}}
        shared.v.app.db.permissions.update_one(query, new)

        await ctx.send(diffify("Granted"))

    @commands.command()
    async def revokePerms(self, ctx, member : commands.MemberConverter, permName : str):
        if not permName in shared.v.app.perms:
            await ctx.send(diffify("Permission invalid"))
            return

        if not self.has_perm(member.id, permName):
            await ctx.send(diffify("User does not hold that permission"))
            return

        query = {"name" : permName}
        new = {"$pull" : {"holders" : member.id}}
        shared.v.app.db.permissions.update_one(query, new)

        await ctx.send(diffify("Revoked"))