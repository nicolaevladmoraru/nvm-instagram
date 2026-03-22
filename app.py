import os
import time
import requests
import cloudinary
import cloudinary.uploader
from flask import Flask, request, jsonify, redirect
from PIL import Image, ImageDraw, ImageFont

app = Flask(__name__)

# ================================
# ENV
# ================================
META_APP_ID = (os.getenv("META_APP_ID") or "").strip()
META_APP_SECRET = (os.getenv("META_APP_SECRET") or "").strip()
META_REDIRECT_URI = (os.getenv("META_REDIRECT_URI") or "").strip()

CLOUDINARY_CLOUD_NAME = (os.getenv("CLOUDINARY_CLOUD_NAME") or "").strip()
CLOUDINARY_API_KEY = (os.getenv("CLOUDINARY_API_KEY") or "").strip()
CLOUDINARY_API_SECRET = (os.getenv("CLOUDINARY_API_SECRET") or "").strip()

IG_USER_ID = (os.getenv("IG_USER_ID") or "").strip()
IG_ACCESS_TOKEN = (os.getenv("IG_ACCESS_TOKEN") or "").strip()

TOKEN_FILE = "/tmp/meta_token.txt"
BASE_URL = "https://graph.facebook.com/v19.0"

# ================================
# CLOUDINARY
# ================================
cloudinary.config(
    cloud_name=CLOUDINARY_CLOUD_NAME,
    api_key=CLOUDINARY_API_KEY,
    api_secret=CLOUDINARY_API_SECRET
)

# ================================
# SAFE FONT
# ================================
def get_font(size, bold=False):
    candidates = []
    if bold:
        candidates = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
        ]
    else:
        candidates = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
        ]

    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass

    return ImageFont.load_default()

# ================================
# META LOGIN
# ================================
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
    if not os.path.exists(TOKEN_FILE):
        return jsonify({"ok": False, "error": "No token saved"}), 404

    with open(TOKEN_FILE, "r", encoding="utf-8") as f:
        token = f.read().strip()

    return jsonify({"ok": True, "token": token})


# ================================
# IMAGE BUILD
# ================================
def build_image(league, home, away, minute, score, pick):
    template_path = "template.png"

    if os.path.exists(template_path):
        img = Image.open(template_path).convert("RGBA")
    else:
        img = Image.new("RGBA", (1080, 1080), (10, 15, 35, 255))

    draw = ImageDraw.Draw(img)

    gold = (242, 196, 78)
    white = (255, 255, 255)

    # text mare si lizibil
    font_title = get_font(64, True)
    font_league = get_font(42, True)
    font_match = get_font(54, True)
    font_label = get_font(42, True)
    font_value = get_font(46, True)

    # title
    draw.text((540, 40), "NVM LIVE ALERT", fill=gold, anchor="mm", font=font_title)

    # league
    draw.text((540, 150), str(league), fill=white, anchor="mm", font=font_league)

    # match
    draw.text((540, 260), f"{home} vs {away}", fill=white, anchor="mm", font=font_match)

    # info
    x_label = 80
    x_value = 420
    y0 = 430
    gap = 120

    draw.text((x_label, y0), "MINUTE:", fill=gold, font=font_label)
    draw.text((x_value, y0), str(minute), fill=white, font=font_value)

    draw.text((x_label, y0 + gap), "SCORE:", fill=gold, font=font_label)
    draw.text((x_value, y0 + gap), str(score), fill=white, font=font_value)

    draw.text((x_label, y0 + gap * 2), "PICK:", fill=gold, font=font_label)
    draw.text((x_value, y0 + gap * 2), str(pick), fill=white, font=font_value)

    filename = f"/tmp/alert_{int(time.time())}.jpg"
    img.convert("RGB").save(filename, "JPEG", quality=95)
    return filename


# ================================
# CLOUDINARY UPLOAD
# ================================
def upload_image(image_path):
    result = cloudinary.uploader.upload(image_path, folder="nvm_instagram")
    return result["secure_url"]


# ================================
# INSTAGRAM POST
# ================================
def get_active_token():
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r", encoding="utf-8") as f:
            token = f.read().strip()
            if token:
                return token
    return IG_ACCESS_TOKEN


def post_to_instagram(image_url, caption):
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

    publish_url = f"{BASE_URL}/{IG_USER_ID}/media_publish"
    publish_payload = {
        "creation_id": creation_id,
        "access_token": access_token
    }

    publish_response = requests.post(publish_url, data=publish_payload, timeout=120).json()
    return publish_response


# ================================
# ROUTES
# ================================
@app.route("/")
def home():
    return "NVM INSTAGRAM LIVE READY"


@app.route("/post-alert", methods=["POST"])
def post_alert():
    try:
        data = request.get_json(force=True) or {}

        # accepta ambele variante de chei
        league = data.get("league", data.get("league_key", ""))
        home = data.get("home", data.get("home_team", ""))
        away = data.get("away", data.get("away_team", ""))
        minute = data.get("minute", "")
        score = data.get("score", "")
        pick = data.get("pick", data.get("pick_text", ""))

        image_path = build_image(league, home, away, minute, score, pick)
        image_url = upload_image(image_path)

        caption = (
            f"{league}\n"
            f"{home} vs {away}\n\n"
            f"Minute: {minute}\n"
            f"Score: {score}\n"
            f"Pick: {pick}\n\n"
            f"@nvm_access_engine_bot"
        )

        result = post_to_instagram(image_url, caption)

        return jsonify({
            "ok": True,
            "image_url": image_url,
            "result": result
        })

    except Exception as e:
        return jsonify({
            "ok": False,
            "error": str(e)
        }), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
