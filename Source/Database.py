import pymongo

client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["mumbleLink"]
users = db["users"]