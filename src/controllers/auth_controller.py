from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from src.models.auth_model import TokenRequest, TokenResponse, UpdateProfileRequest, UserResponse
from src.services.auth_service import (
    verify_google_token,
    authenticate_google_user,
    create_access_token,
    get_current_user_from_token,
    update_user_profile,
    update_user_profile_image,
    upload_profile_image_to_cloudinary,
)

router = APIRouter(tags=["Auth"])
bearer_scheme = HTTPBearer(auto_error=False)


@router.get('/google/login')
def google_login():
    return {"message": "Redirect to Google Sign-In on the client side"}


@router.post('/google/callback', response_model=TokenResponse)
def google_callback(payload: TokenRequest):
    google_user_info = verify_google_token(payload.token)
    if not google_user_info:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Invalid Google token')
        
    user = authenticate_google_user(google_user_info)
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Authentication failed')
        
    token = create_access_token(user['google_id'])
    return TokenResponse(access_token=token)


@router.patch('/me', response_model=UserResponse)
def update_my_profile(
    payload: UpdateProfileRequest,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
):
    if credentials is None or not credentials.credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Not authenticated')

    user = get_current_user_from_token(credentials.credentials)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid or expired token')

    updated_user = update_user_profile(user['google_id'], payload.name, payload.gender)
    if updated_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='User not found')

    updated_user['_id'] = str(updated_user['_id'])
    return UserResponse(**updated_user)


@router.patch('/me/profile-image', response_model=UserResponse)
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

    updated_user = update_user_profile_image(user['google_id'], profile_image_url)
    if updated_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='User not found')

    updated_user['_id'] = str(updated_user['_id'])
    return UserResponse(**updated_user)