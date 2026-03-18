import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

IG_USER_ID = os.getenv("IG_USER_ID", "").strip()
IG_ACCESS_TOKEN = os.getenv("IG_ACCESS_TOKEN", "").strip()


def create_instagram_media(image_url: str, caption: str) -> str:
    url = f"https://graph.facebook.com/v23.0/{IG_USER_ID}/media"
    payload = {
        "image_url": image_url,
        "caption": caption,
        "access_token": IG_ACCESS_TOKEN,
    }
    response = requests.post(url, data=payload, timeout=60)
    response.raise_for_status()
    data = response.json()
    return data["id"]


def publish_instagram_media(creation_id: str) -> dict:
    url = f"https://graph.facebook.com/v23.0/{IG_USER_ID}/media_publish"
    payload = {
        "creation_id": creation_id,
        "access_token": IG_ACCESS_TOKEN,
    }
    response = requests.post(url, data=payload, timeout=60)
    response.raise_for_status()
    return response.json()


@app.route("/", methods=["GET"])
def home():
    return "nvm-instagram running"


@app.route("/post-alert", methods=["POST"])
def post_alert():
    try:
        data = request.get_json(force=True)

        home_team = str(data.get("home_team", "Home")).strip()
        away_team = str(data.get("away_team", "Away")).strip()
        alert_name = str(data.get("alert_name", "LIVE ALERT")).strip()
        minute = str(data.get("minute", "00")).strip()
        score = str(data.get("score", "0 - 0")).strip()
        image_url = str(data.get("image_url", "")).strip()

        if not IG_USER_ID or not IG_ACCESS_TOKEN:
            return jsonify({"ok": False, "error": "Missing IG_USER_ID or IG_ACCESS_TOKEN"}), 500

        if not image_url:
            return jsonify({"ok": False, "error": "image_url is required"}), 400

        caption = (
            f"🚨 NVM ALERT\n\n"
            f"⚽ {home_team} vs {away_team}\n"
            f"⏱ {minute}'\n"
            f"📊 Score: {score}\n"
            f"🎯 {alert_name}\n\n"
            f"📲 Get access: @nvm_access_engine_bot"
        )

        creation_id = create_instagram_media(image_url, caption)
        result = publish_instagram_media(creation_id)

        return jsonify({
            "ok": True,
            "creation_id": creation_id,
            "publish_result": result
        })

    except requests.HTTPError as e:
        try:
            meta_error = e.response.json()
        except Exception:
            meta_error = e.response.text
        return jsonify({"ok": False, "error": "Meta API error", "details": meta_error}), 500

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
