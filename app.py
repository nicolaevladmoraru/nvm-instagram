from flask import Flask, request, jsonify
import requests
import os
import base64
from PIL import Image, ImageDraw, ImageFont
import io

app = Flask(__name__)

IG_USER_ID = os.getenv("IG_USER_ID")
IG_ACCESS_TOKEN = os.getenv("IG_ACCESS_TOKEN")
IMGBB_API_KEY = os.getenv("IMGBB_API_KEY")


# =============================
# GENERATE IMAGE
# =============================
def generate_image(home, away, minute, score, pick):
    width, height = 1080, 1080
    img = Image.new("RGB", (width, height), (10, 20, 40))
    draw = ImageDraw.Draw(img)

    try:
        font_big = ImageFont.truetype("arial.ttf", 80)
        font_mid = ImageFont.truetype("arial.ttf", 50)
        font_small = ImageFont.truetype("arial.ttf", 40)
    except:
        font_big = font_mid = font_small = ImageFont.load_default()

    # Title
    draw.text((100, 100), "NVM LIVE ALERTS", fill=(255, 215, 0), font=font_mid)

    # Match
    draw.text((100, 250), f"{home} vs {away}", fill=(255, 255, 255), font=font_mid)

    # Center info
    draw.text((100, 400), f"Minute: {minute}", fill=(200, 200, 200), font=font_small)
    draw.text((100, 480), f"Score: {score}", fill=(200, 200, 200), font=font_small)

    # PICK
    draw.text((100, 650), f"PICK:", fill=(255, 255, 255), font=font_small)
    draw.text((100, 720), pick, fill=(0, 255, 150), font=font_big)

    # CTA bottom
    draw.text((100, 950), "Join now on Telegram", fill=(255, 255, 255), font=font_small)
    draw.text((100, 1000), "@nvm_access_engine_bot", fill=(0, 200, 255), font=font_small)

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    return buffer


# =============================
# UPLOAD TO IMGBB
# =============================
def upload_to_imgbb(image_buffer):
    encoded = base64.b64encode(image_buffer.read())
    url = "https://api.imgbb.com/1/upload"

    payload = {
        "key": IMGBB_API_KEY,
        "image": encoded
    }

    r = requests.post(url, payload)
    data = r.json()

    return data["data"]["url"]


# =============================
# POST TO INSTAGRAM
# =============================
def post_to_instagram(image_url, caption):
    create_url = f"https://graph.facebook.com/v19.0/{IG_USER_ID}/media"

    create_payload = {
        "image_url": image_url,
        "caption": caption,
        "access_token": IG_ACCESS_TOKEN
    }

    r = requests.post(create_url, data=create_payload)
    creation_id = r.json().get("id")

    publish_url = f"https://graph.facebook.com/v19.0/{IG_USER_ID}/media_publish"

    publish_payload = {
        "creation_id": creation_id,
        "access_token": IG_ACCESS_TOKEN
    }

    requests.post(publish_url, data=publish_payload)


# =============================
# CAPTION GENERATOR
# =============================
def generate_caption(league, home, away, minute, score, pick):
    caption = f"""{league} | {home} vs {away}

⚽ Live Alert  
⏱ Minute: {minute}  
📊 Score: {score}  

🔥 Pick: {pick}

📲 Join now on Telegram:
@nvm_access_engine_bot

#{league.replace(" ", "")} #{home.replace(" ", "")} #{away.replace(" ", "")} #FootballAlerts #LiveBetting #BettingTips #GoalAlert #SoccerTips #NVMProSystem
"""
    return caption


# =============================
# ROUTE
# =============================
@app.route("/post-alert", methods=["POST"])
def post_alert():
    data = request.json

    home = data["home_team"]
    away = data["away_team"]
    minute = data["minute"]
    score = data["score"]
    pick = data["pick"]
    league = data["league"]

    image = generate_image(home, away, minute, score, pick)
    image_url = upload_to_imgbb(image)

    caption = generate_caption(league, home, away, minute, score, pick)

    post_to_instagram(image_url, caption)

    return jsonify({"ok": True})
