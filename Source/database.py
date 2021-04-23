import pymongo
import shared
import logger

class DB():
    def __init__(self, mongoURL):
        print("Initialising db with " + mongoURL)
        self.client = pymongo.MongoClient(mongoURL)
        self.db = self.client["mumble-link"]
        self.tokens = self.db["tokens"]
        self.permissions = self.db["permissions"]
        self.hasInit = self.db["hasInit"]
        self.accounts = self.db["accounts"]
        self.links = self.db["links"]
        self.configs = self.db["configs"]

class Config():
    def __init__(self, key, default):
        self.key = key
        self.default = default
        self.value = default

class Configuration():
    def __init__(self):
        self.configs = [
            Config("welcomeMessage", "Welcome to the Collective/Substrate Mumble Server!"),
            Config("operatingDiscord", 799300028719956039)
        ]

        for config in self.configs:
            if shared.v.app.db.configs.count({"key" : config.key}) > 0:
                config.value = shared.v.app.db.configs.find_one({"key" : config.key})["value"]

    def get(self, key):
        for config in self.configs:
            if config.key == key:
                return config.value

    def change(self, key, value):
        for config in self.configs:
            if config.key == key:
                config.value = value

        shared.v.app.db.configs.update_one({"key" : key}, {"$set" : {"key" : key, "value" : value}}, upsert=True)