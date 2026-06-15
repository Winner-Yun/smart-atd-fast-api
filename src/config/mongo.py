import os

from pymongo import MongoClient


def build_mongo_url() -> str:
    username = os.getenv('MONGO_INITDB_ROOT_USERNAME')
    password = os.getenv('MONGO_INITDB_ROOT_PASSWORD')
    host = os.getenv('MONGO_HOST', 'localhost')
    port = os.getenv('MONGO_PORT', '27017')

    if username and password:
        return f'mongodb://{username}:{password}@{host}:{port}/'

    return f'mongodb://{host}:{port}/'


def collections(name: str):
    url = build_mongo_url()
    client = MongoClient(url)
    return client['smart_atd'][name]