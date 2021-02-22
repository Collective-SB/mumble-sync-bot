import pymongo
import config

client = pymongo.MongoClient(f"mongodb://{config.MONGO_USERNAME}:{config.MONGO_PASSWORD}@localhost:27017/")
db = client["mumbleLink"]
users = db["users"]
allowedRoles = db["roles"]
authorised = db["authorised"]
guilds = db["guilds"]
configs = db["config"]

def saveConfig(key, value):
    query = {"key" : key}
    data = {"$set" : {"key" : key, "value" : value}}

    configs.update_one(query, data, upsert=True)

def getConfig(key):
    query = {"key" : key}
    return configs.find_one(query)["value"]

saveConfig("mumbleSideChannelLink", 2)