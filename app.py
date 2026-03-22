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
# FONT
# ================================
def get_font(size, bold=False):
    paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    ]
    for path in paths:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()

# ================================
# IMAGE BUILD (IMPROVED)
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

    # 🔥 FONTURI MULT MAI MARI
    font_title = get_font(70, True)
    font_league = get_font(50, True)
    font_match = get_font(60, True)
    font_label = get_font(50, True)
    font_value = get_font(56, True)

    # TITLE
    draw.text((540, 60), "NVM LIVE ALERT", fill=gold, anchor="mm", font=font_title)

    # LEAGUE
    draw.text((540, 170), str(league), fill=white, anchor="mm", font=font_league)

    # MATCH (MULT MAI VIZIBIL)
    draw.text((540, 290), f"{home} vs {away}", fill=white, anchor="mm", font=font_match)

    # 🔥 INFO BLOCK (CENTRAT SI MARE)
    y_start = 460
    gap = 140

    # MINUTE
    draw.text((250, y_start), "MINUTE:", fill=gold, anchor="lm", font=font_label)
    draw.text((700, y_start), str(minute), fill=white, anchor="rm", font=font_value)

    # SCORE
    draw.text((250, y_start + gap), "SCORE:", fill=gold, anchor="lm", font=font_label)
    draw.text((700, y_start + gap), str(score), fill=white, anchor="rm", font=font_value)

    # PICK
    draw.text((250, y_start + gap * 2), "PICK:", fill=gold, anchor="lm", font=font_label)
    draw.text((700, y_start + gap * 2), str(pick), fill=white, anchor="rm", font=font_value)

    filename = f"/tmp/alert_{int(time.time())}.jpg"
    img.convert("RGB").save(filename, "JPEG", quality=95)
    return filename

# ================================
# CLOUDINARY
# ================================
def upload_image(image_path):
    result = cloudinary.uploader.upload(image_path, folder="nvm_instagram")
    return result["secure_url"]

# ================================
# TOKEN
# ================================
def get_active_token():
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r", encoding="utf-8") as f:
            token = f.read().strip()
            if token:
                return token
    return IG_ACCESS_TOKEN

# ================================
# INSTAGRAM POST
# ================================
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
        return create_response

    creation_id = create_response["id"]

    # WAIT UNTIL READY
    for _ in range(12):
        status = requests.get(
            f"{BASE_URL}/{creation_id}",
            params={"fields": "status_code", "access_token": access_token}
        ).json()

        if status.get("status_code") == "FINISHED":
            break

        time.sleep(5)

    publish_url = f"{BASE_URL}/{IG_USER_ID}/media_publish"
    return requests.post(
        publish_url,
        data={"creation_id": creation_id, "access_token": access_token}
    ).json()

# ================================
# ROUTE
# ================================
@app.route("/post-alert", methods=["POST"])
def post_alert():
    try:
        data = request.get_json(force=True) or {}

        league = data.get("league", "")
        home = data.get("home", "")
        away = data.get("away", "")
        minute = data.get("minute", "")
        score = data.get("score", "")
        pick = data.get("pick", "")

        # 🔥 folosim caption din live engine
        caption = data.get("caption_message", "")

        if not caption:
            caption = (
                f"{league}\n"
                f"{home} vs {away}\n\n"
                f"Minute: {minute}\n"
                f"Score: {score}\n"
                f"Pick: {pick}\n\n"
                f"@nvm_access_engine_bot"
            )

        image_path = build_image(league, home, away, minute, score, pick)
        image_url = upload_image(image_path)

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
