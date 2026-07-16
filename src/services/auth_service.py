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
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', '15'))
REFRESH_TOKEN_EXPIRE_DAYS = 30
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp'}
ALLOWED_IMAGE_MIMES = {'image/jpeg', 'image/png', 'image/webp'}

# Define the UTC+7 Local Timezone
LOCAL_TZ = datetime.timezone(datetime.timedelta(hours=7))

def get_user_collection():
    return collections('users')

def get_refresh_token_collection():
    return collections('refresh_tokens')

def get_user_by_email(email: str):
    users = get_user_collection()
    return users.find_one({'email': email})

def get_all_users_service(search: str | None = None):
    users = get_user_collection()

    query = {}
    if search:
        query = {
            '$or': [
                {'name': {'$regex': search, '$options': 'i'}},
                {'email': {'$regex': search, '$options': 'i'}}
            ]
        }

    users_cursor = users.find(query).sort('created_at', -1)

    return [
        {
            '_id': str(user['_id']),
            'google_id': user.get('google_id'),
            'email': user.get('email'),
            'name': user.get('name', 'Google User'),
            'avatar': user.get('avatar'),
            'gender': user.get('gender'),
            'provider': user.get('provider', 'google'),
            'status': user.get('status', 'active'),
            'created_at': user.get('created_at'),
            'updated_at': user.get('updated_at')
        }
        for user in users_cursor
    ]

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
    now = datetime.datetime.now(LOCAL_TZ)

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
                'updated_at': datetime.datetime.now(LOCAL_TZ)
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
                'updated_at': datetime.datetime.now(LOCAL_TZ)
            }
        }
    )

    if result.matched_count == 0:
        return None

    return users.find_one({'google_id': google_id})

def validate_image_security(file) -> bool:
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValueError(f"Invalid file extension. Allowed: {', '.join(ALLOWED_IMAGE_EXTENSIONS)}")
        
    if hasattr(file, 'content_type') and file.content_type not in ALLOWED_IMAGE_MIMES:
        raise ValueError(f"Invalid content type. Allowed: {', '.join(ALLOWED_IMAGE_MIMES)}")
   
    file.file.seek(0)
    header = file.file.read(12)
    file.file.seek(0)  
    
    is_valid_signature = False
    
    if header.startswith(b'\xff\xd8\xff'):
        is_valid_signature = True  
    elif header.startswith(b'\x89PNG\r\n\x1a\n'):
        is_valid_signature = True  
    elif header.startswith(b'RIFF') and header[8:12] == b'WEBP':
        is_valid_signature = True  
        
    if not is_valid_signature:
        raise ValueError("File content signature does not match a valid image. Upload rejected.")
        
    return True

def upload_profile_image_to_cloudinary(file):
    validate_image_security(file)
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
        if payload.get('type') == 'refresh':
            return None
    except jwt.PyJWTError:
        return None

    google_id = payload.get('sub')
    if not google_id:
        return None

    return get_user_by_google_id(google_id)

def create_access_token(subject: str):
    now = datetime.datetime.now(LOCAL_TZ)
    expire = now + datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    payload = {
        'sub': subject,
        'iat': now,
        'exp': expire,
        'type': 'access'
    }

    return jwt.encode(payload, JWT_SECRET, algorithm=ALGORITHM)

def create_refresh_token(subject: str) -> str:
    now = datetime.datetime.now(LOCAL_TZ)
    expire = now + datetime.timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    payload = {
        'sub': subject,
        'iat': now,
        'exp': expire,
        'type': 'refresh'
    }
    
    token = jwt.encode(payload, JWT_SECRET, algorithm=ALGORITHM)
    
    get_refresh_token_collection().insert_one({
        'google_id': subject,
        'token': token,
        'expires_at': expire,
        'created_at': now
    })
    
    return token

def verify_refresh_token_service(token: str) -> str | None:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
        if payload.get('type') != 'refresh':
            return None
            
        google_id = payload.get('sub')
        if not google_id:
            return None
            
        db_token = get_refresh_token_collection().find_one({
            'google_id': google_id,
            'token': token
        })
        if not db_token:
            return None
            
        return google_id
    except jwt.PyJWTError:
        return None

def revoke_refresh_token_service(token: str) -> bool:
    result = get_refresh_token_collection().delete_one({'token': token})
    return result.deleted_count > 0