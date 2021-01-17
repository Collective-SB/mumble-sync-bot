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
        user.send_text_message("You must be registered with Mumble to continue. Register then reconnect to continue. Consult the installation guide for help.")

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
            await syncRoles(field, user)

        else:
            # if they are on the system but haven't finished authenticating
            Logger.log(f"Restarting authentication for user who has not finished it. User: {str(user)}")
            user.send_text_message("Hmm, it seems that you're halfway through authenticating. We're going to have to restart that - please follow the instructions:")
            await auth_process(field, user)

async def syncRoles(field, user):
    a=1

async def auth_process(field, user):
    #PM THEM ASKING FOR A DISCORD ID
    user.send_text_message("PM the \"BridgeBot\" with your Discord ID. Make sure to read the instructions!")
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
    user = {"discordID" : response, "mumbleID" : user.get_property("user_id"), "syncToken" : token, "hasAuthenticated": False}
    userToLog = user
    userToLog["syncToken"] = "[REDACTED]"
    Logger.log("Writing: " + str(userToLog))

    Database.users.insert_one(user)
    #THEN PM THEM WITH THE TOKEN AND HAND OFF TO DISCORD TO LISTEN FOR REPLIES

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
        if v.AuthenticationReplies[v.mumble.users[msg.actor].get_property("user_id")] == "NoResponse":
            v.AuthenticationReplies[v.mumble.users[msg.actor].get_property("user_id")] = msg.message