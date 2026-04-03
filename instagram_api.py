import requests

from config import BASE_URL, IG_ACCESS_TOKEN, IG_USER_ID


def get_active_token():
    return IG_ACCESS_TOKEN


def post_to_instagram(image_url: str, caption: str):
    access_token = get_active_token()

    return {
        "debug": True,
        "token_prefix": access_token[:12] if access_token else "",
        "token_suffix": access_token[-12:] if access_token else "",
        "token_length": len(access_token) if access_token else 0,
        "ig_user_id": IG_USER_ID,
        "base_url": BASE_URL,
        "image_url": image_url,
        "caption_preview": caption[:120] if caption else ""
    }
