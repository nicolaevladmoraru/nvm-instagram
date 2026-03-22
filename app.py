import os
import time
import requests
import cloudinary
import cloudinary.uploader
from flask import Flask, request, jsonify
from PIL import Image, ImageDraw, ImageFont

app = Flask(__name__)

# ================================
# CONFIG
# ================================
CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
API_KEY = os.getenv("CLOUDINARY_API_KEY")
API_SECRET = os.getenv("CLOUDINARY_API_SECRET")

IG_ACCESS_TOKEN = os.getenv("IG_ACCESS_TOKEN")
IG_USER_ID = os.getenv("IG_USER_ID")

BASE_URL = "https://graph.facebook.com/v19.0"

cloudinary.config(
    cloud_name=CLOUD_NAME,
    api_key=API_KEY,
    api_secret=API_SECRET
)

# ================================
# FONT SAFE (NO ERRORS)
# ================================
def get_font(size, bold=False):
    paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSans.ttf"
    ]

    for path in paths:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except:
                continue

    return ImageFont.load_default()

# ================================
# BUILD IMAGE (TEXT MARE)
# ================================
def build_image(league, home, away, minute, score, pick):

    width = 1080
    height = 1080

    img = Image.new("RGB", (width, height), (10, 15, 35))
    draw = ImageDraw.Draw(img)

    # FONTS (MARI)
    font_title = get_font(70, True)
    font_big = get_font(80, True)
    font_label = get_font(45, True)
    font_value = get_font(55)

    gold = (255, 215, 0)
    white = (255, 255, 255)

    # ======================
    # TITLE
    # ======================
    draw.text((540, 60), "NVM LIVE ALERT", fill=gold, anchor="mm", font=font_title)

    # ======================
    # LEAGUE
    # ======================
    draw.text((540, 180), league, fill=white, anchor="mm", font=font_big)

    # ======================
    # MATCH
    # ======================
    match_text = f"{home} vs {away}"
    draw.text((540, 300), match_text, fill=white, anchor="mm", font=font_big)

    # ======================
    # DATA
    # ======================
    y_start = 450
    spacing = 120

    # MINUTE
    draw.text((150, y_start), "MINUTE:", fill=gold, font=font_label)
    draw.text((600, y_start), str(minute), fill=white, font=font_value)

    # SCORE
    draw.text((150, y_start + spacing), "SCORE:", fill=gold, font=font_label)
    draw.text((600, y_start + spacing), score, fill=white, font=font_value)

    # PICK
    draw.text((150, y_start + spacing * 2), "PICK:", fill=gold, font=font_label)
    draw.text((600, y_start + spacing * 2), pick, fill=white, font=font_value)

    # ======================
    # SAVE
    # ======================
    filename = f"alert_{int(time.time())}.jpg"
    path = f"/tmp/{filename}"
    img.save(path)

    return path

# ================================
# POST TO INSTAGRAM
# ================================
def post_to_instagram(image_url, caption):

    # STEP 1 - CREATE MEDIA
    url = f"{BASE_URL}/{IG_USER_ID}/media"

    payload = {
        "image_url": image_url,
        "caption": caption,
        "access_token": IG_ACCESS_TOKEN
    }

    res = requests.post(url, data=payload).json()

    if "id" not in res:
        return {"error": "create_media_error", "details": res}

    creation_id = res["id"]

    # STEP 2 - PUBLISH
    publish_url = f"{BASE_URL}/{IG_USER_ID}/media_publish"

    res2 = requests.post(publish_url, data={
        "creation_id": creation_id,
        "access_token": IG_ACCESS_TOKEN
    }).json()

    return res2

# ================================
# ROUTE
# ================================
@app.route("/post-alert", methods=["POST"])
def post_alert():
    try:
        data = request.json

        league = data.get("league", "")
        home = data.get("home", "")
        away = data.get("away", "")
        minute = data.get("minute", "")
        score = data.get("score", "")
        pick = data.get("pick", "")

        # BUILD IMAGE
        image_path = build_image(league, home, away, minute, score, pick)

        # UPLOAD TO CLOUDINARY
        upload = cloudinary.uploader.upload(
            image_path,
            folder="nvm_instagram"
        )

        image_url = upload["secure_url"]

        # CAPTION
        caption = f"""
{league}
{home} vs {away}

Minute: {minute}
Score: {score}
Pick: {pick}

@nvm_access_engine_bot

#Football #LiveAlerts #BettingTips #NVM
        """

        # POST
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
        })


# ================================
# RUN
# ================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
