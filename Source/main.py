import DiscordManager
from threading import *
import InterVars as v
import time
import Logger
import pretty_errors

if __name__ == "__main__":
    Thread(target=DiscordManager.run).start()
    while v.discordReady == False:
        time.sleep(0.01)