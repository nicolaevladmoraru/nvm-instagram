import os
import time
import requests
from flask import Flask, request, jsonify
from PIL import Image, ImageDraw, ImageFont

app = Flask(__name__)

IG_ACCESS_TOKEN = os.getenv("IG_ACCESS_TOKEN")
IG_USER_ID = os.getenv("IG_USER_ID")
IMGBB_API_KEY = os.getenv("IMGBB_API_KEY")


# =============================
# IMAGE SAVE
# =============================
def save_image(img, name):
    path = f"/tmp/{name}_{int(time.time())}.png"
    img.save(path, "PNG")
    return path


# =============================
# BUILD IMAGE FROM TEMPLATE
# =============================
def build_alert_image(league, home, away, minute, score, pick):
    img = Image.open("template.png").convert("RGBA")
    draw = ImageDraw.Draw(img)

    # Fonts (fallback safe)
    try:
        font_league = ImageFont.truetype("arial.ttf", 42)
        font_match = ImageFont.truetype("arialbd.ttf", 70)
        font_info = ImageFont.truetype("arialbd.ttf", 48)
        font_pick = ImageFont.truetype("arialbd.ttf", 52)
    except:
        font_league = font_match = font_info = font_pick = ImageFont.load_default()

    # League
    draw.text((540, 220), league, fill=(255, 255, 255), font=font_league, anchor="mm")

    # Match
    draw.text((540, 330), f"{home} vs {away}", fill=(255, 255, 255), font=font_match, anchor="mm")

    # Minute
    draw.text((230, 470), f"{minute}", fill=(255, 255, 255), font=font_info)

    # Score
    draw.text((230, 560), f"{score}", fill=(255, 255, 255), font=font_info)

    # Pick
    draw.text((230, 650), f"{pick}", fill=(120, 255, 200), font=font_pick)

    return save_image(img, "alert")


# =============================
# UPLOAD TO IMGBB
# =============================
def upload_to_imgbb(image_path):
    with open(image_path, "rb") as f:
        res = requests.post(
            "https://api.imgbb.com/1/upload",
            params={"key": IMGBB_API_KEY},
            files={"image": f},
        )
    return res.json()["data"]["url"]


# =============================
# POST TO INSTAGRAM
# =============================
def post_to_instagram(image_url, caption):
    # Create media
    r = requests.post(
        f"https://graph.facebook.com/v19.0/{IG_USER_ID}/media",
        data={
            "image_url": image_url,
            "caption": caption,
            "access_token": IG_ACCESS_TOKEN,
        },
    ).json()

    creation_id = r.get("id")

    # Wait for processing
    time.sleep(3)

    # Publish
    publish = requests.post(
        f"https://graph.facebook.com/v19.0/{IG_USER_ID}/media_publish",
        data={
            "creation_id": creation_id,
            "access_token": IG_ACCESS_TOKEN,
        },
    ).json()

    return publish


# =============================
# CAPTION
# =============================
def build_caption(league, home, away, minute, score, pick):
    return f"""{league} | {home} vs {away}

⚽ Live Alert
⏱ Minute: {minute}
📊 Score: {score}
🔥 Pick: {pick}

📲 Join now on Telegram:
@nvm_access_engine_bot

#{league.replace(' ', '')} #{home.replace(' ', '')} #{away.replace(' ', '')} #Football #LiveBetting #BettingTips #FootballPredictions #SoccerTips #NVMProSystem
"""


# =============================
# ROUTE
# =============================
@app.route("/post-alert", methods=["POST"])
def post_alert():
    data = request.json

    league = data.get("league")
    home = data.get("home_team")
    away = data.get("away_team")
    minute = data.get("minute")
    score = data.get("score")
    pick = data.get("pick")

    try:
        image_path = build_alert_image(league, home, away, minute, score, pick)
        image_url = upload_to_imgbb(image_path)
        caption = build_caption(league, home, away, minute, score, pick)
        result = post_to_instagram(image_url, caption)

        return jsonify({
            "ok": True,
            "image_url": image_url,
            "result": result
        })

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


# =============================
# HEALTH CHECK
# =============================
@app.route("/")
def home():
    return "Instagram service running"
