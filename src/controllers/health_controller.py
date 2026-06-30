from fastapi import APIRouter, HTTPException
from pymongo import MongoClient, errors

from src.config.mongo import build_mongo_url

router = APIRouter(tags=["Health"])


@router.get('/mongo')
def mongo_health():
    """Ping MongoDB and return connection status."""
    url = build_mongo_url()

    try:
        client = MongoClient(url, serverSelectionTimeoutMS=3000)
        client.admin.command('ping')
        return {'mongo': 'connected'}
    except errors.PyMongoError as exc:
        raise HTTPException(status_code=503, detail=f'MongoDB connection failed: {exc}')
