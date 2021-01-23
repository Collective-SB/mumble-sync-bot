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

server = "161.97.89.8"
nickname = "BridgeBot"
passwd = ""

class pendingReply():
    def __init__(self, mumbleID):
        self.mumbleID = mumbleID
        self.hasResponse = False
        self.responseText = None
        self.id = utilities.generateID(32)

async def connect():
    while v.discordReady == False:
        await asyncio.sleep(0.2)

    v.mumble = pymumble_py3.Mumble(server, nickname, password=passwd, reconnect=True)

    v.mumble.start()

    v.mumble.is_ready()

    #if unregistered, register
    if v.mumble.users.myself.get_property('user_id') == None:
        v.mumble.users.myself.register()

    v.mumble.callbacks.set_callback(pymumble_py3.constants.PYMUMBLE_CLBK_TEXTMESSAGERECEIVED, new_message)
    v.mumble.callbacks.set_callback(pymumble_py3.constants.PYMUMBLE_CLBK_USERCREATED, user_created)

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

    # If unregistered, tell them to register
    if (mumbleID == None):
        user.send_text_message("<h2> You must be registered with Mumble to continue. Register then reconnect to continue.</h2>Consult the installation guide for help.")

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
            await syncRoles(field, user)

        else:
            # if they are on the system but haven't finished authenticating
            Logger.log(f"Restarting authentication for user who has not finished it. User: {str(user)}")
            user.send_text_message("<b>Hmm, it seems that you're halfway through authenticating. Please continue what you were doing.</b>")
            await auth_process(field, user)

async def syncRoles(field, user):
    a=1

async def auth_process(field, user):
    #CHECK YOU DON'T HAVE DUPLICATE PROCESSES
    if user.get_property("user_id") in v.OpenAuthProcesses:
        Logger.log("Not creating auth process because one already exists.")
        return

    user.send_text_message("<h2>You're not authenticated here.</h2>")

    v.OpenAuthProcesses.append(user.get_property("user_id"))
   
    response = await pmQuery("Please PM this bot your Discord ID. Do it by double clicking the bot in the menu on the right.",
    user,
    "Hmm, that doesn't seem like a valid Discord ID.",
    "ID received. Check Discord for a PM.",
    utilities.isValidDiscordID)

    #TODO now do PMing and hand off to Discord
    #GENERATE A TOKEN. WRITE TO THE SYSTEM:
    token = utilities.generateToken()
    toInsert = {"discordID" : response, "mumbleID" : user.get_property("user_id"), "syncToken" : token, "hasAuthenticated": False}
    userToLog = toInsert.copy()
    userToLog["syncToken"] = "[REDACTED]"
    Logger.log("Writing: " + str(userToLog))

    Database.users.insert_one(toInsert)
    #THEN PM THEM WITH THE TOKEN AND WAIT FOR REPLIES
    userD = await DiscordManager.bot.fetch_user(int(response))
    toSend = f"""Hello, I'm the Mumble Link bot. Here's your token:```
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
    if msg.channel_id == [0]:
        name = v.mumble.users[msg.actor]["name"]
        text = utilities.stripHTML(str(msg.message))
        toSend = f"""**{name}** in Mumble:
        {text}
        """
        Logger.log(str(toSend))
        await DiscordManager.bot.get_channel(799300636889186304).send(toSend)

    elif msg.channel_id == []:
        Logger.log(v.PendingReplies)
        userID = v.mumble.users[msg.actor].get_property("user_id")

        for reply in v.PendingReplies:
            if reply.mumbleID == userID:
                reply.responseText = utilities.stripHTML(str(msg.message))
                reply.hasResponse = True
                Logger.log("Added to pending response list.")