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

server = "161.97.89.8"
nickname = "BridgeBot"
passwd = ""

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
            user.send_text_message("<b>Hmm, it seems that you're halfway through authenticating. We're going to have to restart that - please follow the instructions:</b>")
            await auth_process(field, user)

async def syncRoles(field, user):
    a=1

async def auth_process(field, user):
    user.send_text_message("<h2>You're not authenticated here.</h2><p>To register, PM the \"BridgeBot\" with your Discord ID. Make sure to read the instructions!</p>")

     #CHECK YOU DON'T HAVE DUPLICATE PROCESSES
    if user.get_property("user_id") in v.OpenAuthProcesses:
        Logger.log("Not creating auth process because one already exists.")
        return

    v.OpenAuthProcesses.append(user.get_property("user_id"))
   
    #WRITE TO A DICT WHO YOU'RE WAITING FOR RESPONSES FROM
    v.AuthenticationReplies[user.get_property("user_id")] = "NoResponse"
    #CHECK THE DICT TO SEE IF THE NEW_MESSAGE_ASYNC FUNCTION HAS RECORDED ANY REPLIES
    while True:
        await asyncio.sleep(0.2)
        if v.AuthenticationReplies[user.get_property("user_id")] != "NoResponse":
            response = v.AuthenticationReplies[user.get_property("user_id")]
            if utilities.isValidDiscordID(response):
                user.send_text_message("Discord ID has been received. Please check your Discord DMs for a verification token and follow the instructions sent to you.")
                break
            else:
                user.send_text_message("Hmm, that doesn't seem like a valid Discord ID. Please try again, and check the instructions.")
                v.AuthenticationReplies[user.get_property("user_id")] = "NoResponse"

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

    #now wait for a response
    v.TokenReplies[user.get_property("user_id")] = "NoResponse"

    while True:
        await asyncio.sleep(0.2)
        if v.TokenReplies[user.get_property("user_id")] != "NoResponse":
            content = v.TokenReplies[user.get_property("user_id")]

            if content == token:
                Logger.log("User " + str(userToLog) + " accepted and authenticated.")
                query = {"mumbleID" : toInsert.get("mumbleID"), "discordID" : toInsert.get("discordID")}
                newvalues = { "$set": { "hasAuthenticated" : True, "syncToken" : None}}
                Database.users.update_one(query, newvalues)

                user.send_text_message("You have been succesfully authenticated. Your roles should be synced in a moment...")
                await userD.send("Authentication complete. Your token has automatically expired.")
                break
            else:
                user.send_text_message("Unfortunately that's invalid. You sent: " + str(content))
                v.TokenReplies[user.get_property("user_id")] = "NoResponse"

async def new_message_async(msg):
    Logger.log(msg)
    Logger.log(msg.channel_id)
    if msg.channel_id == 0:
        name = v.mumble.users[msg.actor]["name"]
        text = utilities.stripHTML(str(msg.message))
        toSend = f"""**{name}** in Mumble:
        {text}
        """
        Logger.log(str(toSend))
        await DiscordManager.bot.get_channel(799300636889186304).send(toSend)

    elif msg.channel_id == []:
        try:
            if v.AuthenticationReplies[v.mumble.users[msg.actor].get_property("user_id")] == "NoResponse":
                v.AuthenticationReplies[v.mumble.users[msg.actor].get_property("user_id")] = utilities.stripHTML(msg.message)

            if v.TokenReplies[v.mumble.users[msg.actor].get_property("user_id")] == "NoResponse":
                v.TokenReplies[v.mumble.users[msg.actor].get_property("user_id")] = utilities.stripHTML(msg.message)
        except KeyError:
            Logger.log("KeyError in token/ID receive")
            pass