from os import sync
import Logger
import InterVars as v
import Database
import pymumble_py3
import time
from threading import *
import DiscordManager
import asyncio
import utilities
import Database
import copy
import inspect
import config

server = "161.97.89.8"
nickname = "BridgeBot"
passwd = ""

class pendingReply():
    def __init__(self, mumbleID):
        self.mumbleID = mumbleID
        self.hasResponse = False
        self.responseText = None
        self.id = utilities.generateID(32)

def getToken():
    return config.MUMBLE_BOT_TOKEN

async def connect():
    while v.discordReady == False:
        await asyncio.sleep(0.2)

    v.mumble = pymumble_py3.Mumble(server, nickname, password=passwd, reconnect=True, tokens=[getToken()])

    v.mumble.start()

    v.mumble.is_ready()

    v.mumble.callbacks.set_callback(pymumble_py3.constants.PYMUMBLE_CLBK_TEXTMESSAGERECEIVED, new_message)
    v.mumble.callbacks.set_callback(pymumble_py3.constants.PYMUMBLE_CLBK_USERCREATED, user_created)

    v.mumble.channels[Database.getConfig("mainMumbleChannel")].move_in()

    Logger.log("Mumble fully initialised")
    v.mumble.my_channel().send_text_message("Started bridge bot.")

def new_message(msg):
    v.loop.create_task(new_message_async(msg))

def user_created(user):
    v.loop.create_task(user_created_async(user))

async def user_created_async(user):
    #TODO wrap the whole thing in a try/catch and terminate the process if shit goes wrong
    #PSUEDOCODE:
    #IF THEY AREN'T REGISTERED, TELL THEM TO REGISTER
    #IF THEY ARE REGISTERED:
        #IF THEY ARE ON THE SYSTEM BUT ARE NOT FINISHED AUTHENTICATING:
            #AUTH THEM
        #IF THEY ARE ON THE SYSTEM AND HAVE AUTHENTICATED:
            #ROLE SYNC
        #IF THEY ARE NOT ON THE SYSTEM:
            #TELL THEM TO AUTH
    Logger.log(str(user))
    mumbleID = user.get_property("user_id")
    if (mumbleID == 0):
        Logger.log("Not authenticating superuser")
        return

    if (Database.getConfig("DO_AUTHENTICATE") == False):
        await send_with_newlines(user, Database.getConfig("NON_AUTHENTICATE_MESSAGE"))
        await syncRoles()
        return

    # If unregistered, tell them to register
    if (mumbleID == None):
        toSend = """<h2>
Welcome to the Collective mumble server! Please read these instructions carefully: </h2>
You are not yet authenticated. This means we don't know who you actually are, so you don't have access to anything yet.
In order to authenticate you first need to register your account so people can't use your username in the future. To do this:
1. Click "self" at the top bar.
2. Click "register".
3. Click "OK" to keeping your name.

Once you've done that, disconnect and reconnect from the server and you'll be able to carry on with the authentication process.
"""
        user.send_text_message(toSend)

    # if registered, continue.
    else:
        query = {"mumbleID" : mumbleID}
        field = Database.users.find_one(query)

        #if they are not on the system
        if field == None:
            Logger.log(f"Authenticating user {str(user)} who is not on the system.")
            await auth_process(field, user)
            return

        # If they are on the system and have authenticated
        if (field.get("hasAuthenticated") == True):
            Logger.log(f"Succesfully authenticated {str(user)}")
            user.send_text_message("""<div>
<h2> Authentication OK </h2>
<i> Running role resync </i>
</div>""")
            await syncRoles()

        else:
            # if they are on the system but haven't finished authenticating
            Logger.log(f"Restarting authentication for user who has not finished it. User: {str(user)}")
            user.send_text_message("<b>Hmm, it seems that you're halfway through authenticating. Please continue what you were doing.</b>")
            await auth_process(field, user)

async def syncRoles():
    Logger.log("Syncing roles")

    allowedMumbleIDs = []

    guilds = Database.guilds.find()
    for guildID in guilds:
        guild = DiscordManager.bot.get_guild(guildID["guildID"])
        #get list of allowed roles
        allowedRoles = []
        for role in Database.allowedRoles.find():
            allowedRoles.append(role["discordID"])
        
        #write down all allowed mumble IDs by iterating over stored users
        users = Database.users.find()
        
        for user in users:
            discordUserObj = guild.get_member(int(user["discordID"])) #get obj
            if discordUserObj:
                hasAllowedRole = False
                for userRole in discordUserObj.roles:
                    if userRole.id in allowedRoles:
                        hasAllowedRole = True
                        break

                if hasAllowedRole and user["hasAuthenticated"]:
                    allowedMumbleIDs.append(user["mumbleID"])

    Logger.log("Allowed IDs: " + str(allowedMumbleIDs))

    main_channel = v.mumble.channels[Database.getConfig("mainMumbleChannel")]
    root_channel = v.mumble.channels[0]

    main_channel.get_acl()

    for ignore, uobj in v.mumble.users.items():
        uid = None
        try:
            uid = uobj["user_id"]
        except KeyError:
            pass

        if uid:
            if uid in allowedMumbleIDs:
                Logger.log("Adding " + str(uid) + " to authorised")
                main_channel.acl.add_user("bot-sync-authorised", uid)
            else:
                try:
                    Logger.log("Removing " + str(uid) + " from authorised")
                    #DO NOT REMOVE the move call. The del_user fails if they're still in the channel
                    root_channel.move_in(uobj["session"])
                    main_channel.acl.del_user("bot-sync-authorised", uid)
                except ValueError as e:
                    Logger.log("ValueError in auth removal")
                    pass

async def auth_process(field, user):
    #CHECK YOU DON'T HAVE DUPLICATE PROCESSES
    if user.get_property("user_id") in v.OpenAuthProcesses:
        Logger.log("Not creating auth process because one already exists.")
        return

    await send_with_newlines(user, """<h2>You're not authenticated here.</h2>
Now you're registered, you need to prove to us that you're the same person as the Discord user with the same name. This shouldn't take long!

The process goes like this:
1. I will ask you to send me your Discord ID. To get this, enable developer mode in the settings then right click on your name anywhere and click "copy ID. If you need help getting your ID, feel free to ask on Discord.

2. I will send you a token to your Discord account via a private message. This token is <b> secret </b> so don't share it. Instead, copy it.

3. Take the token you copied and PM it to the <b>Mumble side</b> of the bot, like you did with the ID earlier. Make sure it's the bot you're PMing!

4. You should be done! If you have the correct Discord roles you should be shortly given access.
""")

    v.OpenAuthProcesses.append(user.get_property("user_id"))
   
    response = await pmQuery("Please PM this bot your Discord ID. Open a PM it by double clicking the bot in the menu on the right.",
    user,
    "Hmm, that doesn't seem like a valid Discord ID.",
    "ID received. Check Discord for a PM.",
    utilities.isValidDiscordID)

    #GENERATE A TOKEN. WRITE TO THE SYSTEM:
    token = utilities.generateToken()
    toInsert = {"discordID" : response, "mumbleID" : user.get_property("user_id"), "syncToken" : token, "hasAuthenticated": False}
    userToLog = toInsert.copy()
    userToLog["syncToken"] = "[REDACTED]"
    Logger.log("Writing: " + str(userToLog))

    query = {"discordID" : response}
    toInsertUpdate = {"$set" : toInsert}
    Database.users.update_one(query, toInsertUpdate, upsert=True)

    #THEN PM THEM WITH THE TOKEN AND WAIT FOR REPLIES
    userD = await DiscordManager.bot.fetch_user(int(response))
    toSend = f"""Hello, I'm the Mumblecord bot. Here's your token:```
{token}
```Keep this safe and **don't tell anyone.**

In order to complete verification, copy the token and then **DM it to the Mumble bot like you did earlier.**
Make sure you don't accidentally share this, because it could allow someone to make an account in your name.

If you did accidentally share it, disconnect and reconnect from the Mumble server to go through the process again.
That will give you a new token and you can continue as normal. Once you've done that, contact IHave#7106 to make sure nobody used your token."""
    await userD.send(toSend)

    while True:
        response = await pmQuery("Please PM this bot the token you were sent on Discord.", user)
        if response == token:
            Logger.log("User " + str(userToLog) + " accepted and authenticated.")
            
            query = {"mumbleID" : toInsert.get("mumbleID"), "discordID" : toInsert.get("discordID")}
            newvalues = { "$set": { "hasAuthenticated" : True, "syncToken" : None}}
            Database.users.update_one(query, newvalues)

            user.send_text_message("Welcome to Collective's Mumble server! You have been succesfully authenticated and you should be given access in a moment.")
            await userD.send("Authentication complete. Token automatically expired.")
            await userD.send("<:weareone:802506924083511306>")
            break
        else:
            user.send_text_message("Unfortunately that token is invalid :(")

    await syncRoles()

    #remove the open process
    v.OpenAuthProcesses.remove(user.get_property("user_id"))

async def pmQuery(requestText, mumbleUserObj, incorrectAnswerText=None, successMessage=None, verificationCallback=None):
    mumbleID = mumbleUserObj.get_property("user_id")
    
    _pendingReply = pendingReply(mumbleID)

    v.PendingReplies.append(_pendingReply)

    resp = None

    mumbleUserObj.send_text_message(requestText)

    if verificationCallback != None:
        isVerificationAsync = inspect.iscoroutinefunction(verificationCallback)

    while resp == None:
        await asyncio.sleep(0.2)
        for reply in v.PendingReplies:
            if reply.hasResponse == True and reply.mumbleID == mumbleID:
                resp = reply.responseText

                if verificationCallback == None:
                    break

                if isVerificationAsync:
                    verificationCheck = await verificationCallback(resp)
                else:
                    verificationCallback = verificationCallback(resp)

                if verificationCheck:
                    break

                else:
                    mumbleUserObj.send_text_message(incorrectAnswerText)
                    resp = None
                    
                    reply.hasResponse = False
                    reply.responseText = "If you see this, something broke - badly. Tell IHave to fix his bot."

    if successMessage != None:
        mumbleUserObj.send_text_message(successMessage)    
    Logger.log("Got response to query: " + str(resp))

    await deletePendingReply(_pendingReply)
    return resp

async def deletePendingReply(_pendingReply):
    # I feel like there's a bug here but I also can't be bothered to make a lock system on that list
    pendingRepliesCopy = copy.deepcopy(v.PendingReplies)
    i = 0
    for reply in pendingRepliesCopy:
        if reply.id == _pendingReply.id:
            v.PendingReplies.pop(i)
            break

        i = i + 1

async def new_message_async(msg):
    Logger.log(msg)
    Logger.log(msg.channel_id)
    if msg.channel_id == [Database.getConfig("mumbleSideChannelLink")]:
        name = v.mumble.users[msg.actor]["name"]
        text = utilities.stripHTML(str(msg.message))
        toSend = f"""**{name}** in Mumble:
        {text}
        """
        Logger.log(str(toSend))
        await DiscordManager.bot.get_channel(Database.getConfig("messageSyncChannel")).send(toSend)

    elif msg.channel_id == []:
        Logger.log(v.PendingReplies)
        userID = v.mumble.users[msg.actor].get_property("user_id")

        for reply in v.PendingReplies:
            if reply.mumbleID == userID:
                reply.responseText = utilities.stripHTML(str(msg.message))
                reply.hasResponse = True
                Logger.log("Added to pending response list.")

async def send_with_newlines(user, text):
    text = text.split("\n")
    for line in text:
        user.send_text_message(line)
        await asyncio.sleep(0.5)