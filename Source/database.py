import pymongo
import shared
import logger

class DB():
    def __init__(self, mongoURL):
        self.client = pymongo.MongoClient(mongoURL)
        self.db = self.client["mumble-link-v2"]
        self.tokens = self.db["tokens"]
        self.permissions = self.db["permissions"]
        self.hasInit = self.db["hasInit"]
        self.accounts = self.db["accounts"]
        self.links = self.db["links"]

        if self.hasInit.count({}) == 0:
            logger.log("Doing initial db init")
            self.hasInit.insert_one({"hasInit" : False}, {"hasInit" : True})