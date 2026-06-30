import os
from pymongo import MongoClient


def build_mongo_url() -> str:
    mongo_uri = os.getenv("MONGO_URI")

    if mongo_uri:
        return mongo_uri

    username = os.getenv("MONGO_INITDB_ROOT_USERNAME")
    password = os.getenv("MONGO_INITDB_ROOT_PASSWORD")
    host = os.getenv("MONGO_HOST", "localhost")
    port = os.getenv("MONGO_PORT", "27017")

    if username and password:
        return f"mongodb://{username}:{password}@{host}:{port}/"

    return f"mongodb://{host}:{port}/"


def collections(name: str):
    url = build_mongo_url()

    client = MongoClient(
        url,
        tls=True,
        tlsAllowInvalidCertificates=True,
        serverSelectionTimeoutMS=5000,
        connectTimeoutMS=10000,
        retryWrites=True
    )

    return client["smart_atd"][name]