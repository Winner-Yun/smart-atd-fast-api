# src/controllers/auth_controller.py
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from src.models.auth_model import TokenRequest, TokenResponse, UpdateProfileRequest, UserResponse, RefreshTokenRequest
from src.services.auth_service import (
    verify_google_token,
    authenticate_google_user,
    create_access_token,
    create_refresh_token,
    verify_refresh_token_service,
    revoke_refresh_token_service,
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
        
    # Generate both tokens for initial authentication flow
    access_token = create_access_token(user['google_id'])
    refresh_token = create_refresh_token(user['google_id'])
    
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post('/refresh-token', response_model=TokenResponse, summary="Exchange refresh token for a new access token")
def refresh_token_endpoint(payload: RefreshTokenRequest):
    """
    Validates a 30-day refresh token. If it is valid, it uses standard security rotation:
    invalidates the old refresh token and issues a completely clean set of access/refresh pairs.
    """
    google_id = verify_refresh_token_service(payload.refresh_token)
    if not google_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail='Invalid, expired, or revoked refresh token'
        )
        
    # Revoke old refresh token (Token Rotation Practice)
    revoke_refresh_token_service(payload.refresh_token)
    
    # Generate fresh access/refresh pairs
    new_access_token = create_access_token(google_id)
    new_refresh_token = create_refresh_token(google_id)
    
    return TokenResponse(access_token=new_access_token, refresh_token=new_refresh_token)


@router.post('/logout', summary="Revoke a refresh token on session disconnect")
def logout_endpoint(payload: RefreshTokenRequest):
    """
    Explicitly removes the provided refresh token from the database, preventing it from ever being used again.
    """
    revoked = revoke_refresh_token_service(payload.refresh_token)
    if not revoked:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token already invalid or does not exist")
        
    return {"message": "Logged out and token revoked successfully"}


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

@router.get('/me', response_model=UserResponse, summary="Get current user profile")
def get_my_profile(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
):
    """
    Retrieves the profile data for the currently authenticated user.
    """
    if credentials is None or not credentials.credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Not authenticated')

    user = get_current_user_from_token(credentials.credentials)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid or expired token')

    user['_id'] = str(user['_id'])
    
    return UserResponse(**user)