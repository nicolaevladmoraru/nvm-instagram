import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# =========================
# ENV
# =========================
IG_USER_ID = os.getenv("IG_USER_ID", "").strip()
IG_ACCESS_TOKEN = os.getenv("IG_ACCESS_TOKEN", "").strip()
IG_APP_ID = os.getenv("IG_APP_ID", "").strip()
IG_APP_SECRET = os.getenv("IG_APP_SECRET", "").strip()

# For Instagram API with Instagram Login, /me and token exchange are documented
# in Instagram Platform. We keep graph.instagram.com for token/user checks and
# graph.facebook.com for content publishing compatibility.
GRAPH_INSTAGRAM_BASE = "https://graph.instagram.com"
GRAPH_FACEBOOK_BASE = "https://graph.facebook.com/v23.0"


# =========================
# BASIC ROUTES
# =========================
@app.route("/", methods=["GET"])
def home():
    return "nvm-instagram running"


@app.route("/debug-env", methods=["GET"])
def debug_env():
    token = IG_ACCESS_TOKEN or ""
    return jsonify({
        "ig_user_id": IG_USER_ID,
        "token_prefix": token[:8],
        "token_length": len(token),
        "has_app_id": bool(IG_APP_ID),
        "has_app_secret": bool(IG_APP_SECRET),
    })


# =========================
# TOKEN / USER CHECKS
# =========================
def instagram_me(access_token: str) -> dict:
    url = f"{GRAPH_INSTAGRAM_BASE}/me"
    params = {
        "fields": "id,username",
        "access_token": access_token,
    }
    response = requests.get(url, params=params, timeout=60)
    response.raise_for_status()
    return response.json()


@app.route("/debug-me", methods=["GET"])
def debug_me():
    try:
        if not IG_ACCESS_TOKEN:
            return jsonify({"ok": False, "error": "Missing IG_ACCESS_TOKEN"}), 500

        data = instagram_me(IG_ACCESS_TOKEN)
        return jsonify({"ok": True, "me": data})

    except requests.HTTPError as e:
        try:
            details = e.response.json()
        except Exception:
            details = e.response.text
        return jsonify({"ok": False, "error": "Meta API error", "details": details}), 500

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


def exchange_for_long_lived_token(short_lived_token: str) -> dict:
    if not IG_APP_ID or not IG_APP_SECRET:
        raise ValueError("Missing IG_APP_ID or IG_APP_SECRET")

    url = f"{GRAPH_INSTAGRAM_BASE}/access_token"
    params = {
        "grant_type": "ig_exchange_token",
        "client_secret": IG_APP_SECRET,
        "access_token": short_lived_token,
    }
    response = requests.get(url, params=params, timeout=60)
    response.raise_for_status()
    return response.json()


@app.route("/exchange-token", methods=["GET"])
def exchange_token():
    try:
        if not IG_ACCESS_TOKEN:
            return jsonify({"ok": False, "error": "Missing IG_ACCESS_TOKEN"}), 500

        data = exchange_for_long_lived_token(IG_ACCESS_TOKEN)
        return jsonify({"ok": True, "exchange_result": data})

    except requests.HTTPError as e:
        try:
            details = e.response.json()
        except Exception:
            details = e.response.text
        return jsonify({"ok": False, "error": "Meta API error", "details": details}), 500

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


# =========================
# INSTAGRAM PUBLISHING
# =========================
def create_instagram_media(image_url: str, caption: str) -> str:
    url = f"{GRAPH_FACEBOOK_BASE}/{IG_USER_ID}/media"
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
    url = f"{GRAPH_FACEBOOK_BASE}/{IG_USER_ID}/media_publish"
    payload = {
        "creation_id": creation_id,
        "access_token": IG_ACCESS_TOKEN,
    }
    response = requests.post(url, data=payload, timeout=60)
    response.raise_for_status()
    return response.json()


# =========================
# POST ALERT
# =========================
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
            return jsonify({
                "ok": False,
                "error": "Missing IG_USER_ID or IG_ACCESS_TOKEN"
            }), 500

        if not image_url:
            return jsonify({
                "ok": False,
                "error": "image_url is required"
            }), 400

        caption = (
            f"🚨 NVM ALERT\n\n"
            f"⚽ {home_team} vs {away_team}\n"
            f"⏱ {minute}'\n"
            f"📊 Score: {score}\n"
            f"🎯 {alert_name}\n\n"
            f"📲 Get access: @nvm_access_engine_bot"
        )

        creation_id = create_instagram_media(image_url, caption)
        publish_result = publish_instagram_media(creation_id)

        return jsonify({
            "ok": True,
            "creation_id": creation_id,
            "publish_result": publish_result
        })

    except requests.HTTPError as e:
        try:
            details = e.response.json()
        except Exception:
            details = e.response.text

        return jsonify({
            "ok": False,
            "error": "Meta API error",
            "details": details
        }), 500

    except Exception as e:
        return jsonify({
            "ok": False,
            "error": str(e)
        }), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
