from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from src.models.auth import SignUpRequest, LoginRequest, TokenResponse, SignUpResponse, UpdateProfileRequest, UserResponse
from src.services.auth import (
    create_user,
    authenticate_user,
    create_access_token,
    get_current_user_from_token,
    update_user_profile,
    update_user_profile_image,
    upload_profile_image_to_cloudinary,
)

auth_router = APIRouter(tags=["Auth"])
bearer_scheme = HTTPBearer(auto_error=False)


@auth_router.post('/signup', response_model=SignUpResponse)
def signup(payload: SignUpRequest):
    user = create_user(payload.email, payload.password, payload.first_name, payload.last_name)
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Email already registered')
    token = create_access_token(user['email'])
    return SignUpResponse(
        id=str(user['_id']),
        email=user['email'],
        first_name=user['first_name'],
        last_name=user['last_name'],
        gender=user.get('gender'),
        profile_image_url=user.get('profile_image_url'),
        status=user.get('status'),
        created_at=user.get('created_at'),
        access_token=token
    )


@auth_router.post('/login', response_model=TokenResponse)
def login(payload: LoginRequest):
    user = authenticate_user(payload.email, payload.password)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid credentials')
    token = create_access_token(user['email'])
    return TokenResponse(access_token=token)


@auth_router.patch('/me', response_model=UserResponse)
def update_my_profile(
    payload: UpdateProfileRequest,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
):
    if credentials is None or not credentials.credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Not authenticated')

    user = get_current_user_from_token(credentials.credentials)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid or expired token')

    updated_user = update_user_profile(user['email'], payload.first_name, payload.last_name, payload.gender)
    if updated_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='User not found')

    return UserResponse(
        id=str(updated_user['_id']),
        email=updated_user['email'],
        first_name=updated_user['first_name'],
        last_name=updated_user['last_name'],
        gender=updated_user.get('gender'),
        profile_image_url=updated_user.get('profile_image_url'),
        status=updated_user.get('status'),
        created_at=updated_user.get('created_at'),
        updated_at=updated_user.get('updated_at')
    )


@auth_router.patch('/me/profile-image', response_model=UserResponse)
def update_my_profile_image(
    image: UploadFile = File(...),
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
):
    if credentials is None or not credentials.credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Not authenticated')

    user = get_current_user_from_token(credentials.credentials)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid or expired token')

    if not image.content_type or not image.content_type.startswith('image/'):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Please upload an image file')

    try:
        profile_image_url = upload_profile_image_to_cloudinary(image)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f'Image upload failed: {exc}')

    updated_user = update_user_profile_image(user['email'], profile_image_url)
    if updated_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='User not found')

    return UserResponse(
        id=str(updated_user['_id']),
        email=updated_user['email'],
        first_name=updated_user['first_name'],
        last_name=updated_user['last_name'],
        gender=updated_user.get('gender'),
        profile_image_url=updated_user.get('profile_image_url'),
        status=updated_user.get('status'),
        created_at=updated_user.get('created_at'),
        updated_at=updated_user.get('updated_at')
    )
