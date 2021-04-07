import pymongo
import shared

class DB():
    def __init__(self, mongoURL):
        self.client = pymongo.MongoClient(mongoURL)
        self.db = self.client["mumble-link-v2"]
        self.tokens = self.db["tokens"]
        self.permissions = self.db["permissions"]
        self.hasInit = self.db["hasInit"]

        for perm in shared.v.app.perms:
            exists = self.permissions.count({"name" : perm}) > 0
            if not exists:
                self.permissions.insert_one({"name" : perm, "holders" : []})

        if self.hasInit.count({}) == 0:
            print("Doing initial db init")
            self.hasInit.insert_one({"hasInit" : False}, {"hasInit" : True})