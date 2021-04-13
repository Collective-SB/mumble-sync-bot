import pymumble_py3
import asyncio
import shared

class MumbleInstance():
    def __init__(self, ip, nick):
        self.ip = ip
        self.nick = nick
        self.loop = asyncio.get_event_loop()

    async def start(self):
        self.instance = pymumble_py3.Mumble(self.ip, self.nick, reconnect=True, certfile="cert.pem", keyfile="key.pem")

        self.instance.start()

        self.instance.is_ready()

        self.instance.users.myself.register()

        self.instance.my_channel().send_text_message("Bridge bot initialised and connected.")

        print(str(self.instance.users))

        self.removeFromGroup("tempgroup", 45)

        while True:
            print("Done")
            await asyncio.sleep(1)

    def addToGroup(self, groupName, mumbleID):
        root = self.instance.channels[0]
        root.get_acl()

        root.acl.add_user(groupName, mumbleID)

    def removeFromGroup(self, groupName, mumbleID):
        root = self.instance.channels[0]
        root.get_acl()

        root.acl.del_user(groupName, mumbleID)

inst = MumbleInstance("161.97.89.8", "BridgeBot9000")

asyncio.get_event_loop().create_task(inst.start())

asyncio.get_event_loop().run_forever()