import os
import requests
from flask import Flask, redirect, request, jsonify

app = Flask(__name__)

APP_ID = os.getenv("META_APP_ID")
APP_SECRET = os.getenv("META_APP_SECRET")
REDIRECT_URI = os.getenv("META_REDIRECT_URI")

ACCESS_TOKEN_FILE = "/tmp/meta_token.txt"


# =============================
# LOGIN START
# =============================
@app.route("/meta-login")
def meta_login():
    url = (
        f"https://www.facebook.com/v19.0/dialog/oauth"
        f"?client_id={APP_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&scope=instagram_basic,instagram_content_publish,pages_show_list,pages_read_engagement"
    )
    return redirect(url)


# =============================
# CALLBACK (TOKEN GENERATOR)
# =============================
@app.route("/meta-callback")
def meta_callback():
    code = request.args.get("code")

    if not code:
        return "No code received"

    token_url = (
        f"https://graph.facebook.com/v19.0/oauth/access_token"
        f"?client_id={APP_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&client_secret={APP_SECRET}"
        f"&code={code}"
    )

    res = requests.get(token_url).json()

    if "access_token" not in res:
        return jsonify(res)

    access_token = res["access_token"]

    # SAVE TOKEN
    with open(ACCESS_TOKEN_FILE, "w") as f:
        f.write(access_token)

    return {
        "ok": True,
        "access_token": access_token
    }


# =============================
# GET SAVED TOKEN
# =============================
@app.route("/get-token")
def get_token():
    if not os.path.exists(ACCESS_TOKEN_FILE):
        return {"error": "No token saved"}

    with open(ACCESS_TOKEN_FILE) as f:
        return {"token": f.read()}


@app.route("/")
def home():
    return "Meta login system ready"
