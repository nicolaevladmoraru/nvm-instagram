import os
import time
import requests
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
# SIMPLE TEXT WRAP
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


# =============================
# BUILD IMAGE FROM TEMPLATE
# =============================
def build_alert_image(league_key, home_team, away_team, minute, score, pick_text):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    img_path = os.path.join(base_dir, "template.png")

    img = Image.open(img_path).convert("RGBA")
    draw = ImageDraw.Draw(img)

    gold = (242, 196, 78)
    white = (255, 255, 255)
    mint = (170, 235, 245)

    # === FONTS (UPDATED SIZES) ===
    font_league = get_font(52, bold=True)
    font_match = get_font(90, bold=True)
    font_label = get_font(60, bold=True)
    font_value = get_font(60, bold=True)
    font_pick = get_font(70, bold=True)

    # --- LEAGUE ---
    league_lines = wrap_text(draw, str(league_key), font_league, 800)
    y = 230
    for line in league_lines[:2]:
        draw.text((540, y), line, fill=white, font=font_league, anchor="mm")
        y += 60

    # --- MATCH ---
    match_text = f"{home_team} vs {away_team}"
    match_lines = wrap_text(draw, match_text, font_match, 850)
    y = 380
    for line in match_lines[:2]:
        draw.text((540, y), line, fill=white, font=font_match, anchor="mm")
        y += 95

    # --- INFO BLOCK ---
    label_x = 100
    value_x = 420

    # MINUTE
    draw.text((label_x, 580), "MINUTE:", fill=gold, font=font_label)
    draw.text((value_x, 580), str(minute), fill=white, font=font_value)

    # SCORE
    draw.text((label_x, 690), "SCORE:", fill=gold, font=font_label)
    draw.text((value_x, 690), str(score), fill=white, font=font_value)

    # PICK
    draw.text((label_x, 800), "PICK:", fill=gold, font=font_label)

    pick_lines = wrap_text(draw, str(pick_text), font_pick, 500)
    y = 800
    for idx, line in enumerate(pick_lines[:2]):
        draw.text((value_x, y + idx * 75), line, fill=mint, font=font_pick)

    return save_image(img, "alert")


# =============================
# BUILD REPORT IMAGE
# =============================
def build_report_image(title, period_label, message):
    width, height = 1080, 1350
    img = Image.new("RGB", (width, height), (11, 20, 39))
    draw = ImageDraw.Draw(img)

    gold = (242, 196, 78)
    white = (245, 247, 250)
    blue = (70, 130, 220)
    gray = (182, 190, 200)

    draw.rounded_rectangle((36, 36, 1044, 1314), radius=34, outline=blue, width=4)

    font_title = get_font(56, bold=True)
    font_sub = get_font(34, bold=True)
    font_text = get_font(28, bold=False)
    font_small = get_font(30, bold=False)

    draw.text((60, 60), str(title), font=font_title, fill=gold)
    draw.text((60, 138), str(period_label), font=font_sub, fill=gray)

    y = 220
    for paragraph in str(message or "").split("\n"):
        paragraph = paragraph.strip()
        if paragraph == "":
            y += 16
            continue

        wrapped = wrap_text(draw, paragraph, font_text, 920)

        for line in wrapped:
            draw.text((60, y), line, font=font_text, fill=white)
            y += 38

        y += 4
        if y > 1180:
            break

    draw.text((60, 1240), "Join now on Telegram", font=get_font(34, bold=True), fill=gold)
    draw.text((60, 1284), "@nvm_access_engine_bot", font=font_small, fill=white)

    return save_image(img, "report")


# =============================
# UPLOAD TO IMGBB
# =============================
def upload_to_imgbb(image_path):
    with open(image_path, "rb") as f:
        res = requests.post(
            "https://api.imgbb.com/1/upload",
            params={"key": IMGBB_API_KEY},
            files={"image": f},
            timeout=120,
        )
    res.raise_for_status()
    data = res.json()
    return data["data"]["url"]


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
    response.raise_for_status()
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
    response.raise_for_status()
    return response.json()


def wait_until_media_ready(creation_id, max_attempts=10, delay_seconds=4):
    last_status = {}
    time.sleep(5)

    for _ in range(max_attempts):
        last_status = get_container_status(creation_id)
        status_code = str(last_status.get("status_code", "")).upper()

        if status_code == "FINISHED":
            return last_status

        if status_code == "ERROR":
            raise RuntimeError(f"Media container failed: {last_status}")

        time.sleep(delay_seconds)

    raise RuntimeError(f"Media not ready in time: {last_status}")


def publish_media_container(creation_id):
    response = requests.post(
        f"https://graph.instagram.com/{IG_USER_ID}/media_publish",
        data={
            "creation_id": creation_id,
            "access_token": IG_ACCESS_TOKEN,
        },
        timeout=120,
    )
    response.raise_for_status()
    return response.json()


# =============================
# CAPTIONS
# =============================
def sanitize_hashtag(text):
    cleaned = "".join(ch for ch in str(text or "") if ch.isalnum())
    return cleaned


def build_alert_caption(league_key, home_team, away_team, minute, score, pick_text):
    title = f"{league_key} | {home_team} vs {away_team}".strip(" |")

    hashtags = [
        f"#{sanitize_hashtag(league_key)}",
        f"#{sanitize_hashtag(home_team)}",
        f"#{sanitize_hashtag(away_team)}",
        "#FootballAlerts",
        "#LiveBetting",
        "#BettingTips",
        "#FootballPredictions",
        "#SoccerTips",
        "#GoalAlert",
        "#LiveAlerts",
        "#NVMProSystem",
    ]

    return f"""{title}

⚽ Live Alert
⏱ Minute: {minute}
📊 Score: {score}
🔥 Pick: {pick_text}

📲 Join now on Telegram:
@nvm_access_engine_bot

{" ".join(hashtags)}
""".strip()


def build_report_caption(title, period_label):
    return f"""{title}
📅 {period_label}

📲 Join now on Telegram:
@nvm_access_engine_bot

#FootballAlerts #LiveAlerts #BettingTips #FootballPredictions #SoccerTips #NVMProSystem
""".strip()


# =============================
# ROUTES
# =============================
@app.route("/")
def home():
    return "Instagram service running"


@app.route("/debug-env")
def debug_env():
    return jsonify({
        "has_imgbb": bool(IMGBB_API_KEY),
        "ig_user_id": IG_USER_ID,
        "token_length": len(IG_ACCESS_TOKEN),
        "token_prefix": IG_ACCESS_TOKEN[:8] if IG_ACCESS_TOKEN else "",
    })


@app.route("/post-alert", methods=["POST"])
def post_alert():
    try:
        data = request.get_json(force=True) or {}

        league_key = str(data.get("league_key", "")).strip()
        home_team = str(data.get("home_team", "")).strip()
        away_team = str(data.get("away_team", "")).strip()
        minute = str(data.get("minute", "")).strip()
        score = str(data.get("score", "")).strip()
        pick_text = str(data.get("pick_text", "")).strip()

        if not league_key:
            league_key = "Live Football"
        if not home_team:
            home_team = "Home"
        if not away_team:
            away_team = "Away"
        if not minute:
            minute = "00"
        if not score:
            score = "0 - 0"
        if not pick_text:
            pick_text = "Over 0.5 Goals"

        image_path = build_alert_image(
            league_key=league_key,
            home_team=home_team,
            away_team=away_team,
            minute=minute,
            score=score,
            pick_text=pick_text,
        )

        image_url = upload_to_imgbb(image_path)
        caption = build_alert_caption(
            league_key=league_key,
            home_team=home_team,
            away_team=away_team,
            minute=minute,
            score=score,
            pick_text=pick_text,
        )

        creation_id = create_media_container(image_url, caption)
        status_result = wait_until_media_ready(creation_id)
        publish_result = publish_media_container(creation_id)

        return jsonify({
            "ok": True,
            "image_url": image_url,
            "caption": caption,
            "creation_id": creation_id,
            "status_result": status_result,
            "publish_result": publish_result,
        })

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/post-report", methods=["POST"])
def post_report():
    try:
        data = request.get_json(force=True) or {}

        title = str(data.get("title", "NVM LIVE ALERTS DAILY REPORT")).strip()
        period_label = str(data.get("period_label", "")).strip()
        message = str(data.get("message", "")).strip()

        if not period_label:
            period_label = "Daily Report"
        if not message:
            message = "No alerts for this period."

        image_path = build_report_image(title, period_label, message)
        image_url = upload_to_imgbb(image_path)
        caption = build_report_caption(title, period_label)

        creation_id = create_media_container(image_url, caption)
        status_result = wait_until_media_ready(creation_id)
        publish_result = publish_media_container(creation_id)

        return jsonify({
            "ok": True,
            "image_url": image_url,
            "caption": caption,
            "creation_id": creation_id,
            "status_result": status_result,
            "publish_result": publish_result,
        })

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
