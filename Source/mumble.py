import pymumble_py3
import asyncio
import shared
import time
import utilities

class MumbleInstance():
    def __init__(self, token, ip, nick):
        self.token = token
        self.ip = ip
        self.nick = nick
        self.loop = asyncio.get_event_loop()

    async def start(self):
        self.instance = pymumble_py3.Mumble(self.ip, self.nick, reconnect=True)

        self.instance.start()

        self.instance.is_ready()

        self.instance.my_channel().send_text_message("Bridge bot initialised and connected.")
        print("Bridge bot started")

        self.instance.callbacks.set_callback(pymumble_py3.constants.PYMUMBLE_CLBK_TEXTMESSAGERECEIVED, self._newMessageCallback_)

        while True:
            await asyncio.sleep(1)

    def _newMessageCallback_(self, event):
        if hasattr(event, "session") and len(event.session) > 0:
            self.loop.create_task(self.onDM(event))
            return

        self.loop.create_task(self.onMessage(event))

    async def onMessage(self, event):
        print("Received channel text message")

    async def onDM(self, event):
        print("Received DM: " + str(event))

        text = utilities.stripHTML(event.message)
        userObj = self.instance.users[event.actor]

        exists = shared.v.app.db.tokens.count({"text" : text}) > 0

        if exists:
            content = shared.v.app.db.tokens.find_one({"text" : text})

            if time.time() > content["created"] + 3600:
                userObj.send_text_message("<b> Unfortunately, that token is expired. </b>")
                return

            userObj.send_text_message("You should now be registered on Mumble and your internal account created...")

        else:
            userObj.send_text_message("Token is invalid.")