import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

_client = None


def get_collection():
    global _client

    if _client is None:
        mongo_uri = os.getenv("MONGO_URI")
        _client = MongoClient(mongo_uri)

    db_name = os.getenv("MONGO_DB_NAME")
    collection_name = os.getenv("MONGO_COLLECTION_NAME")

    db = _client[db_name]
    return db[collection_name]


def clear_collection():
    collection = get_collection()
    collection.delete_many({})
