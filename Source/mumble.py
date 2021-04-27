import pymumbleinternal.pymumble_py3 as pymumble
import asyncio
import shared
import time
import utilities
import logger
import discordClient
from threading import *

class MumbleInstance():
    def __init__(self, ip, nick):
        self.ip = ip
        self.nick = nick
        self.loop = asyncio.get_event_loop()

    async def start(self):
        self.instance = pymumble.Mumble(self.ip, self.nick, reconnect=True, certfile="cert.pem", keyfile="key.pem")

        self.instance.start()

        self.instance.is_ready()

        self.instance.users.myself.register()

        self.instance.my_channel().send_text_message("Bridge bot initialised and connected.")
        logger.log("Bridge bot started")

        self.instance.callbacks.set_callback(pymumble.constants.PYMUMBLE_CLBK_TEXTMESSAGERECEIVED, self._newMessageCallback_)
        self.instance.callbacks.set_callback(pymumble.constants.PYMUMBLE_CLBK_USERCREATED, self.on_join)
        self.instance.callbacks.set_callback(pymumble.constants.PYMUMBLE_CLBK_ACLRECEIVED, self.acl_received)

        while True:
            await asyncio.sleep(1)
        
    def acl_received(self, event):
        logger.log("Received ACL change for event " + str(event))

    def on_join(self, event):
        print(str(event))
        logger.log("Join Event: " + str(event))

        uid = event.get("user_id")

        self.get_user_by_id(uid).send_text_message(shared.v.app.config.get("welcomeMessage"))
        if uid:
            discordClient.client.loop.create_task(self.sync(mumbleID=uid))

    def del_user(self, channel, group, uid):
        Thread(target=channel.acl.del_user, args=(group, uid)).start()

    def add_user(self, channel, group, uid):
        Thread(target=channel.acl.add_user, args=(group, uid)).start()

    def _newMessageCallback_(self, event):
        if hasattr(event, "session") and len(event.session) > 0:
            self.loop.create_task(self.onDM(event))
            return

        self.loop.create_task(self.onMessage(event))

    async def onMessage(self, event):
        logger.log("Received channel text message")

    async def onDM(self, event):
        logger.log("Received DM: " + str(event))

        text = utilities.stripHTML(event.message)
        userObj = self.instance.users[event.actor]

        exists = shared.v.app.db.tokens.count({"text" : text}) > 0

        if exists:
            content = shared.v.app.db.tokens.find_one({"text" : text})

            if time.time() > content["created"] + 3600:
                userObj.send_text_message("<b> Unfortunately, that token is expired. </b>")
                return

            if not self.is_registered(userObj):
                userObj.send_text_message("Please register with Mumble beforehand. You can do this under 'self'.")
            else:
                if shared.v.app.db.accounts.count({"discordID" : content["uid"]}) > 0:
                    userObj.send_text_message("Account already exists")
                    return

                self.createAccount(content["uid"], userObj.get_property("user_id"))
                shared.v.app.db.tokens.delete_many({"uid" : content["uid"]})
                userObj.send_text_message("Account created.")
                userObj.send_text_message("Please leave and join the server for syncing to occur.")
        else:
            userObj.send_text_message("Token is invalid.")

    def is_registered(self, obj):
        return obj.get_property("user_id") != None

    def createAccount(self, discordID, mumbleID):
        shared.v.app.db.accounts.insert_one({"discordID" : discordID, "mumbleID" : mumbleID, "createdTime" : time.time()})

    async def sync(self, discordID=None, mumbleID=None):
        #Note: It seems to reliably remove them, provided it's me that adds them manually, not the bot automatically. Odd.
        startTime = time.time()

        if discordID:
            account = shared.v.app.db.accounts.find_one({"discordID" : discordID})
        if mumbleID:
            account = shared.v.app.db.accounts.find_one({"mumbleID" : mumbleID})

        if not mumbleID and not discordID:
            return "Should supply a ID"

        guild = await discordClient.client.fetch_guild(int(shared.v.app.operatingDiscord))
        member = await guild.fetch_member(int(account["discordID"]))

        allowedPerms = []
        
        for role in member.roles:
            logger.log("Scanning role: " + str(role) + " for " + str(account))
            if shared.v.app.db.links.count({"roleID" : str(role.id)}) > 0:
                data = shared.v.app.db.links.find_one({"roleID" : str(role.id)})

                allowedPerms.append(data["groupName"])

        root = self.instance.channels[0]

        #they need to be moved to root and back or they can't remove perms. Yes it's stupid.
        oldChannel = self.get_channel_by_id(self.get_user_by_id(account["mumbleID"]).get_property("channel_id"))
        changedChannel = False

        for link in shared.v.app.db.links.find({}):
            if self.get_user_by_id(account["mumbleID"]).get_property("channel_id") != 0:
                    root.move_in(self.get_user_by_id(account["mumbleID"]).get_property("session"))
                    changedChannel = True
                    await asyncio.sleep(0.1)
                    logger.log(f"Moving user {account['mumbleID']} into root channel to allow for permission assignment")

            await asyncio.sleep(0.3)
            
            if link["groupName"] in allowedPerms:
                self.add_user(root, link["groupName"], account["mumbleID"])
                logger.log(f"Adding user {account['mumbleID']} mumble side, {account['discordID']} discord with {link['groupName']}")
            else:
                logger.log(f"Removing user {account['mumbleID']} mumble side, {account['discordID']} discord with {link['groupName']}")

                self.del_user(root, link["groupName"], account["mumbleID"])
                await asyncio.sleep(0.1)
                logger.log("Removed")

        if changedChannel:
            oldChannel.move_in(self.get_user_by_id(account["mumbleID"]).get_property("session"))

        endTime = time.time()

        logger.log("Sync completed in " + str(1000 *(endTime - startTime)) + "ms")

        self.get_user_by_id(account["mumbleID"]).send_text_message("Sync complete.")

    def get_user_by_id(self, _id):
        for u in self.instance.users:
            user = self.instance.users[u]

            if user.get_property("user_id") == _id:
                return user

    def get_channel_by_id(self, _id):
        return self.instance.channels[_id]