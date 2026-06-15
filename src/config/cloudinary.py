import os

import cloudinary


def configure_cloudinary_client() -> None:
    cloud_name = os.getenv('CDN_NAME')
    api_key = os.getenv('CDN_API_KEY')
    api_secret = os.getenv('CDN_API_SECRET')

    if not cloud_name or not api_key or not api_secret:
        raise ValueError('Cloudinary credentials are missing from the environment')

    cloudinary.config(
        cloud_name=cloud_name,
        api_key=api_key,
        api_secret=api_secret,
        secure=True,
    )
