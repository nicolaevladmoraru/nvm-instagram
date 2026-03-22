import requests
from flask import Flask, jsonify, redirect, request

from config import BASE_URL, META_APP_ID, META_APP_SECRET, META_REDIRECT_URI, TOKEN_FILE
from routes_alerts import alerts_bp
from routes_reports import reports_bp

app = Flask(__name__)

app.register_blueprint(alerts_bp)
app.register_blueprint(reports_bp)


@app.route("/")
def home():
    return "NVM INSTAGRAM LIVE READY"


@app.route("/meta-login")
def meta_login():
    login_url = (
        f"https://www.facebook.com/v19.0/dialog/oauth"
        f"?client_id={META_APP_ID}"
        f"&redirect_uri={META_REDIRECT_URI}"
        f"&scope=pages_show_list,pages_read_engagement,instagram_basic,instagram_content_publish"
    )
    return redirect(login_url)


@app.route("/meta-callback")
def meta_callback():
    code = request.args.get("code")
    if not code:
        return jsonify({"ok": False, "error": "No code received"}), 400

    token_url = (
        f"{BASE_URL}/oauth/access_token"
        f"?client_id={META_APP_ID}"
        f"&redirect_uri={META_REDIRECT_URI}"
        f"&client_secret={META_APP_SECRET}"
        f"&code={code}"
    )

    try:
        response = requests.get(token_url, timeout=60)
        data = response.json()
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

    if "access_token" not in data:
        return jsonify({"ok": False, "details": data}), 400

    access_token = data["access_token"]

    with open(TOKEN_FILE, "w", encoding="utf-8") as f:
        f.write(access_token)

    return jsonify({
        "ok": True,
        "message": "Token generated and saved.",
        "access_token": access_token
    })


@app.route("/get-token")
def get_token():
    import os

    if not os.path.exists(TOKEN_FILE):
        return jsonify({"ok": False, "error": "No token saved"}), 404

    with open(TOKEN_FILE, "r", encoding="utf-8") as f:
        token = f.read().strip()

    return jsonify({"ok": True, "token": token})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
