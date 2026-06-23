import pymongo
from django.conf import settings

_client = None

def get_db():
    global _client
    if _client is None:
        _client = pymongo.MongoClient(
            settings.MONGODB_URI,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
            socketTimeoutMS=5000,
            tls=True,
            tlsAllowInvalidCertificates=False
        )
    return _client[settings.MONGODB_DB]

def get_collection(name):
    return get_db()[name]