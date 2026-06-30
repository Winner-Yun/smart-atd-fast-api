import os
import datetime
import jwt
import cloudinary
import cloudinary.uploader
from google.oauth2 import id_token
from google.auth.transport import requests

from src.config.cloudinary import configure_cloudinary_client
from src.config.mongo import collections

JWT_SECRET = os.getenv('JWT_SECRET', 'please-change-me')
ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', '60'))
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')


def get_user_collection():
    return collections('users')

def get_user_by_email(email: str):
    users = get_user_collection()
    return users.find_one({'email': email})

def verify_google_token(token: str) -> dict | None:
    try:
        idinfo = id_token.verify_oauth2_token(token, requests.Request(), GOOGLE_CLIENT_ID)
        return idinfo if idinfo.get('email_verified', False) else None
    except ValueError:
        return None


def authenticate_google_user(google_user_info: dict) -> dict | None:
    users = get_user_collection()
    
    google_id = google_user_info.get('sub')
    email = google_user_info.get('email')
    name = google_user_info.get('name', 'Google User')
    avatar = google_user_info.get('picture')

    if not google_id or not email:
        return None

    user = users.find_one({'$or': [{'google_id': google_id}, {'email': email}]})
    now = datetime.datetime.now(datetime.timezone.utc)

    if user:
        update_data = {'updated_at': now}
        unset_data = {}
        
        if 'password' in user:
            unset_data['password'] = ""
            
        if 'name' not in user:
            first_name = user.get('first_name', '')
            last_name = user.get('last_name', '')
            update_data['name'] = f"{first_name} {last_name}".strip() or name
            unset_data['first_name'] = ""
            unset_data['last_name'] = ""

        if 'avatar' not in user and 'profile_image_url' in user:
            update_data['avatar'] = user.get('profile_image_url') or avatar
            unset_data['profile_image_url'] = ""
        elif 'avatar' not in user:
            update_data['avatar'] = avatar

        if user.get('provider') != 'google' or 'google_id' not in user:
            update_data['google_id'] = google_id
            update_data['provider'] = 'google'

        update_query = {'$set': update_data}
        if unset_data:
            update_query['$unset'] = unset_data

        users.update_one({'_id': user['_id']}, update_query)
        return users.find_one({'_id': user['_id']})

    new_user_doc = {
        'google_id': google_id,
        'email': email,
        'name': name,
        'avatar': avatar,
        'gender': None,
        'provider': 'google',
        'status': 'active',
        'created_at': now,
        'updated_at': now
    }

    res = users.insert_one(new_user_doc)
    new_user_doc['_id'] = res.inserted_id

    return new_user_doc


def get_user_by_google_id(google_id: str):
    users = get_user_collection()
    return users.find_one({'google_id': google_id})


def update_user_profile(google_id: str, name: str, gender: str | None):
    users = get_user_collection()
    result = users.update_one(
        {'google_id': google_id},
        {
            '$set': {
                'name': name,
                'gender': gender,
                'updated_at': datetime.datetime.now(datetime.timezone.utc)
            }
        }
    )

    if result.matched_count == 0:
        return None

    return users.find_one({'google_id': google_id})


def update_user_profile_image(google_id: str, avatar_url: str):
    users = get_user_collection()
    result = users.update_one(
        {'google_id': google_id},
        {
            '$set': {
                'avatar': avatar_url,
                'updated_at': datetime.datetime.now(datetime.timezone.utc)
            }
        }
    )

    if result.matched_count == 0:
        return None

    return users.find_one({'google_id': google_id})


def upload_profile_image_to_cloudinary(file):
    configure_cloudinary_client()
    file.file.seek(0)
    upload_result = cloudinary.uploader.upload(
        file.file,
        folder='smart-atd/user_profile',
        resource_type='image',
        overwrite=True,
        unique_filename=True
    )
    return upload_result.get('secure_url')


def get_current_user_from_token(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        return None

    google_id = payload.get('sub')
    if not google_id:
        return None

    return get_user_by_google_id(google_id)


def create_access_token(subject: str):
    now = datetime.datetime.now(datetime.timezone.utc)
    expire = now + datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    payload = {
        'sub': subject,
        'iat': now,
        'exp': expire
    }

    return jwt.encode(payload, JWT_SECRET, algorithm=ALGORITHM)