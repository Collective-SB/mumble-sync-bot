import os
import mumble
import asyncio
from dotenv import load_dotenv
import discordClient
import database
import shared

class Application():
    def get_config(self, name):
        return os.environ[name]

    def init_perms(self):
        for perm in self.perms:
            dbPerms = self.db.permissions.find({})
            exists = False
            for i in dbPerms:
                if i["name"] == perm:
                    exists = True
                    break

            if not exists:
                self.db.permissions.insert_one({"name" : perm, "holders" : []})

    def init(self):
        load_dotenv()
        self.perms = ["admin", "mumbleManager"]
        self.db = database.DB(self.get_config("mongoUrl"))
        self.init_perms()
        self.discordToken = self.get_config("discordToken")
        self.ip = self.get_config("mumbleIP")
        self.nick = self.get_config("mumbleNick")
        self.mumbleInstance = mumble.MumbleInstance(self.ip, self.nick)
        self.operatingDiscord = self.get_config("operatingDiscord")
        self.config = database.Configuration()

    def start(self):
        discordClient.client.loop.create_task(self.mumbleInstance.start())
        discordClient.client.run(self.discordToken)

if __name__ == "__main__":
    shared.v.app = Application()
    shared.v.app.init()
    shared.v.app.start()