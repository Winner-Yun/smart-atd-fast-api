import os
import datetime
import hashlib

import bcrypt
import cloudinary
import cloudinary.uploader
import jwt

from src.config.cloudinary import configure_cloudinary_client
from src.config.mongo import collections

JWT_SECRET = os.getenv('JWT_SECRET', 'please-change-me')
ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', '60'))


def get_user_collection():
    return collections('users')


def hash_password(password: str) -> str:
    password_digest = hashlib.sha256(password.encode('utf-8')).digest()
    hashed = bcrypt.hashpw(password_digest, bcrypt.gensalt())
    return f'sha256${hashed.decode("utf-8")}'


def verify_password(plain_password: str, hashed_password: str) -> bool:
    if hashed_password.startswith('sha256$'):
        stored_hash = hashed_password.removeprefix('sha256$').encode('utf-8')
        password_digest = hashlib.sha256(plain_password.encode('utf-8')).digest()
        return bcrypt.checkpw(password_digest, stored_hash)

    return bcrypt.checkpw(
        plain_password.encode('utf-8'),
        hashed_password.encode('utf-8')
    )


def create_user(email: str, password: str, first_name: str, last_name: str):
    users = get_user_collection()

    if users.find_one({'email': email}):
        return None

    hashed = hash_password(password)

    doc = {
        'email': email,
        'password': hashed,
        'first_name': first_name,
        'last_name': last_name,
        'gender': None,
        'profile_image_url': None,
        'status': 'active',
        'created_at': datetime.datetime.now(datetime.timezone.utc)
    }

    res = users.insert_one(doc)
    doc['_id'] = res.inserted_id

    return doc


def authenticate_user(email: str, password: str):
    users = get_user_collection()

    user = users.find_one({'email': email})
    if not user:
        return None

    if not verify_password(password, user.get('password', '')):
        return None

    return user


def get_user_by_email(email: str):
    users = get_user_collection()
    return users.find_one({'email': email})


def update_user_profile(email: str, first_name: str, last_name: str, gender: str | None):
    users = get_user_collection()

    result = users.update_one(
        {'email': email},
        {
            '$set': {
                'first_name': first_name,
                'last_name': last_name,
                'gender': gender,
                'updated_at': datetime.datetime.now(datetime.timezone.utc)
            }
        }
    )

    if result.matched_count == 0:
        return None

    return users.find_one({'email': email})


def update_user_profile_image(email: str, profile_image_url: str):
    users = get_user_collection()

    result = users.update_one(
        {'email': email},
        {
            '$set': {
                'profile_image_url': profile_image_url,
                'updated_at': datetime.datetime.now(datetime.timezone.utc)
            }
        }
    )

    print(f"matched: {result.matched_count}")
    print(f"modified: {result.modified_count}")

    if result.matched_count == 0:
        return None

    return users.find_one({'email': email})


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
        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[ALGORITHM]
        )
    except jwt.PyJWTError:
        return None

    email = payload.get('sub')

    if not email:
        return None

    return get_user_by_email(email)


def create_access_token(subject: str):
    now = datetime.datetime.now(datetime.timezone.utc)
    expire = now + datetime.timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        'sub': subject,
        'iat': now,
        'exp': expire
    }

    return jwt.encode(
        payload,
        JWT_SECRET,
        algorithm=ALGORITHM
    )