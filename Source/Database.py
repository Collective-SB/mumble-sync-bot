import pymongo
import config

client = pymongo.MongoClient(config.MONGO_URL)
db = client["mumble-link"]
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
