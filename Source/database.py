from typing import KeysView
import pymongo
import shared
import logger

class DB():
    def __init__(self, mongoURL):
        self.client = pymongo.MongoClient(mongoURL)
        self.db = self.client["mumbleLink"]
        self.tokens = self.db["tokens"]
        self.permissions = self.db["permissions"]
        self.hasInit = self.db["hasInit"]
        self.accounts = self.db["accounts"]
        self.links = self.db["links"]
        self.configs = self.db["configs"]

        if self.hasInit.count({}) == 0:
            logger.log("Doing initial db init")
            self.hasInit.insert_one({"hasInit" : False}, {"hasInit" : True})

class Config():
    def __init__(self, key, default):
        self.key = key
        self.default = default
        self.value = default

class Configuration():
    def __init__(self):
        self.configs = [
            Config("welcomeMessage", "Welcome to the Collective/Substrate Mumble Server!")
        ]

        for config in self.configs:
            if shared.v.app.db.configs.count({"key" : config.key}) > 0:
                config.value = shared.v.app.db.configs.find_one({"key" : config.key})

    def get(self, key):
        for config in self.configs:
            if config.key == key:
                return config.value