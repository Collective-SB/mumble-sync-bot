import os
import mumble
import asyncio
from dotenv import load_dotenv
import discordClient
import database
import shared

class Application():
    def getConfig(self, name):
        return os.environ[name]

    def init(self):
        load_dotenv()
        self.perms = ["admin", "mumbleManager"]
        self.db = database.DB("mongodb://localhost:27017/")
        self.discordToken = self.getConfig("discordToken")
        self.mumbleToken = self.getConfig("mumbleToken")
        self.ip = self.getConfig("mumbleIP")
        self.nick = self.getConfig("mumbleNick")
        self.mumbleInstance = mumble.MumbleInstance(self.mumbleToken, self.ip, self.nick)

    def start(self):
        loop = asyncio.get_event_loop()

        loop.create_task(self.mumbleInstance.start())
        discordClient.client.run(self.discordToken)

        loop.run_forever()

if __name__ == "__main__":
    shared.v.app = Application()
    shared.v.app.init()
    shared.v.app.start()