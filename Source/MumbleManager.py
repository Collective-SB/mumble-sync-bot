import Logger
import InterVars as v
import Database
import pymumble_py3
import time
from threading import *
import DiscordManager
import asyncio
import utilities

server = "161.97.89.8"
nickname = "BridgeBot"
passwd = ""

async def connect():
    while v.discordReady == False:
        await asyncio.sleep(0.2)
        print("Waiting for Discord to ready")

    v.mumble = pymumble_py3.Mumble(server, nickname, password=passwd)

    v.mumble.start()

    v.mumble.is_ready()

    v.mumble.callbacks.set_callback(pymumble_py3.constants.PYMUMBLE_CLBK_TEXTMESSAGERECEIVED, new_message)

    Logger.log("Mumble fully initialised")

def new_message(msg):
    v.loop.create_task(new_message_async(msg))

async def new_message_async(msg):
    name = v.mumble.users[msg.actor]["name"]
    text = utilities.stripHTML(str(msg.message))
    toSend = f"""**{name}** in Mumble:
    {text}
    """
    print(str(toSend))
    await DiscordManager.bot.get_channel(799300636889186304).send(toSend)