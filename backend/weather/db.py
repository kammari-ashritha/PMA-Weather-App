import pymongo
from django.conf import settings

_client = None

def get_db():
    global _client
    if _client is None:
        _client = pymongo.MongoClient(settings.MONGODB_URI)
    return _client[settings.MONGODB_DB]

def get_collection(name):
    return get_db()[name]