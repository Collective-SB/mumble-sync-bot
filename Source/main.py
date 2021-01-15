import DiscordManager
from threading import *
import InterVars as v
import time
import Logger

if __name__ == "__main__":
    Thread(target=DiscordManager.run).start()
    while v.botManager.ready == False:
        time.sleep(0.01)