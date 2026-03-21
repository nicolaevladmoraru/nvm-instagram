import os
import time
from flask import Flask, request, jsonify, send_file, abort
import requests
from PIL import Image, ImageDraw, ImageFont

app = Flask(__name__)

IG_ACCESS_TOKEN = (os.getenv("IG_ACCESS_TOKEN") or "").strip()
IG_USER_ID = (os.getenv("IG_USER_ID") or "").strip()

TMP_DIR = "/tmp"


# =============================
# IMAGE SAVE
# =============================
def save_image(img, name):
    filename = f"{name}_{int(time.time())}.jpg"
    path = os.path.join(TMP_DIR, filename)

    rgb_img = img.convert("RGB")
    rgb_img.save(path, "JPEG", quality=95)

    return path, filename


# =============================
# FONT HELPERS
# =============================
def get_font(size: int, bold: bool = False):
    candidates = []
    if bold:
        candidates = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
        ]
    else:
        candidates = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/dejavu/DejaVuSans.ttf",
        ]

    for path in candidates:
        if os.path.exists(path):
            return ImageFont.truetype(path, size=size)

    return ImageFont.load_default()


# =============================
# TEXT HELPERS
# =============================
def wrap_text(draw, text, font, max_width):
    words = str(text or "").split()
    if not words:
        return [""]

    lines = []
    current = words[0]

    for word in words[1:]:
        test = f"{current} {word}"
        bbox = draw.textbbox((0, 0), test, font=font)
        width = bbox[2] - bbox[0]

        if width <= max_width:
            current = test
        else:
            lines.append(current)
            current = word

    lines.append(current)
    return lines


def center_text(draw, y, text, font, fill):
    draw.text((540, y), str(text), fill=fill, font=font, anchor="ma")


# =============================
# COLORS
# =============================
GOLD = (242, 196, 78)
WHITE = (255, 255, 255)
GREEN = (120, 255, 120)
RED = (255, 80, 80)


# =============================
# BUILD ALERT IMAGE
# =============================
def build_alert_image(league_key, home_team, away_team, minute, score, pick_text):
    img = Image.open("template.png").convert("RGBA")
    draw = ImageDraw.Draw(img)

    font_title = get_font(27, bold=True)
    font_league = get_font(19, bold=True)
    font_match = get_font(23, bold=True)
    font_label = get_font(20, bold=True)
    font_value = get_font(20, bold=True)

    center_text(draw, 20, "NVM LIVE ALERT", font_title, GOLD)

    league_lines = wrap_text(draw, str(league_key), font_league, 900)[:2]
    league_y = 75
    for line in league_lines:
        center_text(draw, league_y, line, font_league, WHITE)
        league_y += 22

    match_text = f"{home_team} vs {away_team}"
    match_lines = wrap_text(draw, match_text, font_match, 900)[:2]
    match_y = 110
    for line in match_lines:
        center_text(draw, match_y, line, font_match, WHITE)
        match_y += 26

    label_x = 35
    value_x = 205

    draw.text((label_x, 185), "MINUTE:", fill=GOLD, font=font_label)
    draw.text((label_x, 220), "SCORE:", fill=GOLD, font=font_label)
    draw.text((label_x, 280), "PICK:", fill=GOLD, font=font_label)

    draw.text((value_x, 185), str(minute), fill=WHITE, font=font_value)
    draw.text((value_x, 220), str(score), fill=WHITE, font=font_value)

    pick_lines = wrap_text(draw, str(pick_text), font_value, 420)
    pick_y = 280
    for idx, line in enumerate(pick_lines[:2]):
        draw.text((value_x, pick_y + idx * 24), line, fill=GOLD, font=font_value)

    return save_image(img, "alert")


# =============================
# BUILD REPORT IMAGE
# =============================
def build_report_image(title, date_text, wins, lost, winrate):
    img = Image.open("template.png").convert("RGBA")
    draw = ImageDraw.Draw(img)

    font_title = get_font(27, bold=True)
    font_date = get_font(23, bold=True)
    font_label = get_font(20, bold=True)
    font_value = get_font(20, bold=True)

    center_text(draw, 20, str(title), font_title, GOLD)
    center_text(draw, 110, str(date_text), font_date, WHITE)

    label_x = 35
    value_x = 205

    draw.text((label_x, 185), "WINS:", fill=GREEN, font=font_label)
    draw.text((label_x, 220), "LOST:", fill=RED, font=font_label)
    draw.text((label_x, 280), "WIN RATE:", fill=GOLD, font=font_label)

    draw.text((value_x, 185), str(wins), fill=WHITE, font=font_value)
    draw.text((value_x, 220), str(lost), fill=WHITE, font=font_value)
    draw.text((value_x, 280), str(winrate), fill=WHITE, font=font_value)

    return save_image(img, "report")


# =============================
# INSTAGRAM HELPERS
# =============================
def create_media_container(image_url, caption):
    response = requests.post(
        f"https://graph.instagram.com/{IG_USER_ID}/media",
        data={
            "image_url": image_url,
            "caption": caption,
            "access_token": IG_ACCESS_TOKEN,
        },
        timeout=120,
    )

    print("create_media_container:", response.status_code, response.text)

    if response.status_code != 200:
        raise RuntimeError(
            f"Meta create media error | image_url={image_url} | response={response.text}"
        )

    return response.json()["id"]


def get_container_status(creation_id):
    response = requests.get(
        f"https://graph.instagram.com/{creation_id}",
        params={
            "fields": "id,status_code",
            "access_token": IG_ACCESS_TOKEN,
        },
        timeout=60,
    )
    return response.json()


def wait_until_media_ready(creation_id):
    time.sleep(5)

    for _ in range(10):
        status = get_container_status(creation_id)
        if status.get("status_code") == "FINISHED":
            return status
        time.sleep(3)

    raise RuntimeError("Media not ready")


def publish_media_container(creation_id):
    response = requests.post(
        f"https://graph.instagram.com/{IG_USER_ID}/media_publish",
        data={
            "creation_id": creation_id,
            "access_token": IG_ACCESS_TOKEN,
        },
        timeout=120,
    )

    print("publish:", response.status_code, response.text)

    if response.status_code != 200:
        raise RuntimeError(response.text)

    return response.json()


# =============================
# MEDIA ROUTE
# =============================
@app.route("/media/<filename>")
def serve_media(filename):
    path = os.path.join(TMP_DIR, filename)
    if not os.path.exists(path):
        abort(404)
    return send_file(path, mimetype="image/jpeg")


# =============================
# ROUTES
# =============================
@app.route("/")
def home():
    return "Instagram service running"


@app.route("/post-alert", methods=["POST"])
def post_alert():
    try:
        data = request.get_json(force=True) or {}

        image_path, filename = build_alert_image(
            data.get("league_key", "League"),
            data.get("home_team", "Home"),
            data.get("away_team", "Away"),
            data.get("minute", "00"),
            data.get("score", "0 - 0"),
            data.get("pick_text", "Over 0.5 Goals"),
        )

        base_url = request.url_root.rstrip("/")
        if base_url.startswith("http://"):
            base_url = "https://" + base_url[len("http://"):]

        image_url = f"{base_url}/media/{filename}"
        print("IMAGE URL:", image_url)

        caption = "NVM LIVE ALERT"

        creation_id = create_media_container(image_url, caption)
        wait_until_media_ready(creation_id)
        publish = publish_media_container(creation_id)

        return jsonify({"ok": True, "image_url": image_url, "publish": publish})

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
