import os
import time
import requests
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from PIL import Image, ImageDraw, ImageFont

app = Flask(__name__)

IG_ACCESS_TOKEN = (os.getenv("IG_ACCESS_TOKEN") or "").strip()
IG_USER_ID = (os.getenv("IG_USER_ID") or "").strip()
IMGBB_API_KEY = (os.getenv("IMGBB_API_KEY") or "").strip()


# =============================
# IMAGE SAVE
# =============================
def save_image(img, name):
    path = f"/tmp/{name}_{int(time.time())}.png"
    img.save(path, "PNG")
    return path


# =============================
# FONT
# =============================
def get_font(size, bold=False):
    if bold:
        path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    else:
        path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

    return ImageFont.truetype(path, size=size)


# =============================
# ALERT TEMPLATE (FINAL DESIGN)
# =============================
def build_alert_image(league, home, away, minute, score, pick):

    img = Image.open("template.png").convert("RGBA")
    draw = ImageDraw.Draw(img)

    gold = (242, 196, 78)
    white = (255, 255, 255)

    # === FONTS ===
    f_title = get_font(27, True)
    f_league = get_font(19, True)
    f_match = get_font(23, True)
    f_label = get_font(20, True)
    f_value = get_font(20, True)

    center_x = 540

    # TITLE
    draw.text((center_x, 20), "NVM LIVE ALERT", fill=gold, font=f_title, anchor="mm")

    # LEAGUE
    draw.text((center_x, 75), league, fill=white, font=f_league, anchor="mm")

    # MATCH
    match = f"{home} vs {away}"
    draw.text((center_x, 110), match, fill=white, font=f_match, anchor="mm")

    # LABELS
    draw.text((35, 185), "MINUTE:", fill=gold, font=f_label)
    draw.text((35, 220), "SCORE:", fill=gold, font=f_label)
    draw.text((35, 280), "PICK:", fill=gold, font=f_label)

    # VALUES
    draw.text((200, 185), str(minute), fill=white, font=f_value)
    draw.text((200, 220), str(score), fill=white, font=f_value)
    draw.text((200, 280), str(pick), fill=gold, font=f_value)

    return save_image(img, "alert")


# =============================
# REPORT TEMPLATE
# =============================
def build_report_image(title, date_text, wins, lost, winrate):

    img = Image.open("template.png").convert("RGBA")
    draw = ImageDraw.Draw(img)

    gold = (242, 196, 78)
    white = (255, 255, 255)
    green = (0, 255, 120)
    red = (255, 80, 80)

    f_title = get_font(27, True)
    f_date = get_font(23, True)
    f_label = get_font(20, True)
    f_value = get_font(20, True)

    center_x = 540

    # TITLE
    draw.text((center_x, 20), title, fill=gold, font=f_title, anchor="mm")

    # DATE / PERIOD
    draw.text((center_x, 110), date_text, fill=white, font=f_date, anchor="mm")

    # STATS
    draw.text((35, 185), "WINS:", fill=gold, font=f_label)
    draw.text((200, 185), str(wins), fill=green, font=f_value)

    draw.text((35, 220), "LOST:", fill=gold, font=f_label)
    draw.text((200, 220), str(lost), fill=red, font=f_value)

    draw.text((35, 280), "WIN RATE:", fill=gold, font=f_label)
    draw.text((200, 280), str(winrate), fill=gold, font=f_value)

    return save_image(img, "report")


# =============================
# UPLOAD
# =============================
def upload_to_imgbb(path):
    with open(path, "rb") as f:
        r = requests.post(
            "https://api.imgbb.com/1/upload",
            params={"key": IMGBB_API_KEY},
            files={"image": f},
        )
    return r.json()["data"]["url"]


# =============================
# INSTAGRAM POST
# =============================
def post_to_instagram(image_url, caption):

    r = requests.post(
        f"https://graph.instagram.com/{IG_USER_ID}/media",
        data={
            "image_url": image_url,
            "caption": caption,
            "access_token": IG_ACCESS_TOKEN,
        },
    )

    creation_id = r.json()["id"]

    time.sleep(5)

    requests.post(
        f"https://graph.instagram.com/{IG_USER_ID}/media_publish",
        data={
            "creation_id": creation_id,
            "access_token": IG_ACCESS_TOKEN,
        },
    )


# =============================
# ALERT ENDPOINT (FREE → IG)
# =============================
@app.route("/post-alert", methods=["POST"])
def post_alert():
    d = request.json

    img = build_alert_image(
        d["league"],
        d["home"],
        d["away"],
        d["minute"],
        d["score"],
        d["pick"],
    )

    url = upload_to_imgbb(img)

    caption = f"""
⚽ LIVE ALERT

{d["home"]} vs {d["away"]}
Minute: {d["minute"]}
Score: {d["score"]}
Pick: {d["pick"]}

📲 @nvm_access_engine_bot
"""

    post_to_instagram(url, caption)

    return {"ok": True}


# =============================
# DAILY / WEEKLY / MONTHLY / MILESTONE
# =============================
@app.route("/post-report", methods=["POST"])
def post_report():

    d = request.json

    img = build_report_image(
        d["title"],      # NVM DAILY REPORT / WEEKLY / etc
        d["date"],       # 21/03/2026 or range
        d["wins"],
        d["lost"],
        d["winrate"],
    )

    url = upload_to_imgbb(img)

    caption = f"""
{d["title"]}

{d["date"]}

Wins: {d["wins"]}
Lost: {d["lost"]}
Win Rate: {d["winrate"]}

📲 @nvm_access_engine_bot
"""

    post_to_instagram(url, caption)

    return {"ok": True}


# =============================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
