# Smart ATD Backend

FastAPI backend service for Smart ATD.

## Run The API

```sh
# local development
uvicorn main:app --reload --port 8000

# production
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## Required Environment Variables

```env
APP_ENV=local

MONGO_HOST=localhost
MONGO_PORT=27017
MONGO_INITDB_ROOT_USERNAME=your_username
MONGO_INITDB_ROOT_PASSWORD=your_password

JWT_SECRET=please-change-me
ACCESS_TOKEN_EXPIRE_MINUTES=60

CDN_NAME=your_cloudinary_cloud_name
CDN_API_KEY=your_cloudinary_api_key
CDN_API_SECRET=your_cloudinary_api_secret
```
