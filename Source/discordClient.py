import asyncio
from logging import log
from discord import client, Game
from discord.ext import commands
from secrets import token_urlsafe
import base64
import shared
import contextlib
import io
import time
import logger

ownerID = 318756837266554881

def holds(permName):
    def predicate(ctx):
        if ctx.author.id == ownerID and shared.v.permOverride:
            return True
        if shared.v.app:
            return shared.v.app.db.permissions.count({"name" : permName, "holders" : ctx.author.id}) > 0
        else:
            return False

    return commands.check(predicate)

def owner():
    def predicate(ctx):
        if ctx.author.id == ownerID:
            return True

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

async def pushLogLoop():
    while True:
        toSend = ""
        count = 0
        for text in logger.backlog:
            if len(toSend) + len(text) < 1970:
                toSend = toSend + "\n" + text
                count += 1
            else:
                break
        
        if count > 0:
            del logger.backlog[:count]

            await client.get_channel(799300592270442546).send("```\n" + toSend + "\n```")
            print(toSend)

            await asyncio.sleep(2)

        else:
            await asyncio.sleep(0.2)

#I fucking hate this but the docs literally all run by this.
client = commands.Bot(command_prefix="#")

@client.event
async def on_ready():
    logger.log(f"Logged on as {client.user}")
    client.add_cog(Utility(client))
    client.add_cog(AccountLinking(client))
    client.add_cog(Permissions(client))
    client.add_cog(PermLinks(client))
    client.loop.create_task(pushLogLoop())

class Utility(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command()
    async def answer(self, ctx):
        await ctx.send(diffify("42"))

    @owner()
    @commands.command()
    async def evaluate(self, ctx, *, code):
        str_obj = io.StringIO() #Retrieves a stream of data
        try:
            with contextlib.redirect_stdout(str_obj):
                exec(code)
        except Exception as e:
            return await ctx.send(f"python{e.__class__.__name__}: {e}")
        await ctx.send(f'{str_obj.getvalue()}')

    @holds("admin")
    @commands.command()
    async def config(self, ctx, key, value):
        #TODO implement
        await ctx.send("Command not yet implemented")

class AccountLinking(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command()
    async def linkAccount(self, ctx):
        token = createToken()
        shared.v.app.db.tokens.insert_one({"text" : token, "uid" : str(ctx.author.id), "created" : time.time()})
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
    
    @holds("admin")
    @commands.command()
    async def listUserPerms(self, ctx, user : commands.MemberConverter):
        perms = shared.v.app.db.permissions.find({"holders" : user.id})
        text = ""
        for perm in perms:
            text += perm["name"] + "\n"

        if text == "":
            text = "No Permissions"

        await ctx.send(diffify(text))

    @holds("admin")
    @commands.command()
    async def listAllPerms(self, ctx):
        perms = shared.v.app.db.permissions.find({})

        text = ""
        for perm in perms:
            text += perm["name"] + "\n"

        await ctx.send(diffify(text))

    @holds("admin")
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

    @holds("admin")
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

    @owner()
    @commands.command()
    async def override(self, ctx, status):
        if status == "status":
            await ctx.send(diffify(str(shared.v.permOverride)))

        elif status == "on":
            shared.v.permOverride = True
            await ctx.send(diffify("Enabled"))

        elif status == "off":
            shared.v.permOverride = False
            await ctx.send(diffify("Disabled"))

class PermLinks(commands.Cog):
    def __init__(self, client):
        self.client = client

    #TODO let you supply a symbol that all channels that have the ACL should start with
    @holds("mumbleManager")
    @commands.command()
    async def linkGroup(self, ctx, groupName, roleID):
        query = {"groupName" : groupName}
        update = {"groupName" : groupName.lower(), "roleID" : roleID}
        shared.v.app.db.links.update(query, update, upsert=True)

        await ctx.send(diffify("Done"))

    @holds("mumbleManager")
    @commands.command()
    async def unlinkGroup(self, ctx, groupName):
        query = {"groupName" : groupName.lower()}
        shared.v.app.db.links.delete_many(query)

        await ctx.send(diffify("Done"))

    @holds("mumbleManager")
    @commands.command()
    async def addToGroup(self, ctx):
        shared.v.app.mumbleInstance.addToGroup("tempgroup", 45)

    @holds("mumbleManager")
    @commands.command()
    async def removeFromGroup(self, ctx):
        shared.v.app.mumbleInstance.removeFromGroup("tempgroup", 45)