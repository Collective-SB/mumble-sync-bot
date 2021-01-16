class User(self, discordID, mumbleID, discordNick, mumbleNick, permission):
    discordID = None
    mumbleID = None
    discordNick = None
    mumbleNick = None
    permission = None
    
    def __init__(self, discordID, mumbleID, discordNick, mumbleNick, permissions):
        self.discordID = discordID
        self.mumbleID = mumbleID
        self.discordNick = discordNick
        self.mumbleNick = mumbleNick
        self.permissions = permissions

    def getDiscordNick():
        if self.discordNick != None:
            return self.discordNick
        else:
            #TODO actually get from ID

    def getMumbleNick():
        if self.MumbleNick != None:
            return self.mumbleNick
        else:
            #TODO actually get from ID