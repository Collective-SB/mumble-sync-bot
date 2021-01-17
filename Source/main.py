import DiscordManager
from threading import *
import InterVars as v
import time
import MumbleManager
import Logger
import asyncio

if __name__ == "__main__":
    v.loop = asyncio.get_event_loop()
    token = DiscordManager.getToken()

    v.loop.create_task(DiscordManager.bot.start(token))

    v.loop.create_task(MumbleManager.connect())
    v.loop.create_task(Logger.pushLogLoop())

    v.loop.run_forever()