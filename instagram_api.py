import os
import time
import requests

from config import BASE_URL, IG_ACCESS_TOKEN, IG_USER_ID, TOKEN_FILE


def get_active_token():
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r", encoding="utf-8") as f:
            token = f.read().strip()
            if token:
                return token
    return IG_ACCESS_TOKEN


def post_to_instagram(image_url: str, caption: str):
    access_token = get_active_token()

    create_url = f"{BASE_URL}/{IG_USER_ID}/media"
    create_payload = {
        "image_url": image_url,
        "caption": caption,
        "access_token": access_token
    }

    create_response = requests.post(create_url, data=create_payload, timeout=120).json()

    if "id" not in create_response:
        return {"error": "create_media_error", "details": create_response}

    creation_id = create_response["id"]

    for _ in range(12):
        status_response = requests.get(
            f"{BASE_URL}/{creation_id}",
            params={"fields": "status_code", "access_token": access_token},
            timeout=60
        ).json()

        status_code = str(status_response.get("status_code", "")).upper()

        if status_code == "FINISHED":
            break

        if status_code == "ERROR":
            return {"error": "media_status_error", "details": status_response}

        time.sleep(5)

    publish_url = f"{BASE_URL}/{IG_USER_ID}/media_publish"
    publish_payload = {
        "creation_id": creation_id,
        "access_token": access_token
    }

    publish_response = requests.post(publish_url, data=publish_payload, timeout=120).json()
    return publish_response
