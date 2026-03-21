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

    # TITLE
    center_text(draw, 20, "NVM LIVE ALERT", font_title, GOLD)

    # LEAGUE
    league_lines = wrap_text(draw, str(league_key), font_league, 900)
    league_lines = league_lines[:2]
    league_y = 75
    for line in league_lines:
        center_text(draw, league_y, line, font_league, WHITE)
        league_y += 22

    # MATCH
    match_text = f"{home_team} vs {away_team}"
    match_lines = wrap_text(draw, match_text, font_match, 900)
    match_lines = match_lines[:2]
    match_y = 110
    for line in match_lines:
        center_text(draw, match_y, line, font_match, WHITE)
        match_y += 26

    # LABELS + VALUES
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

    # TITLE
    center_text(draw, 20, str(title), font_title, GOLD)

    # DATE / RANGE / MILESTONE
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
    print("upload_to_imgbb:", res.status_code, res.text[:500])
    res.raise_for_status()
    data = res.json()
    return data["data"]["url"]


# =============================
# INSTAGRAM HELPERS
# =============================
def create_media_container(image_url, caption):
    response = requests.post(
        f"https://graph.facebook.com/v25.0/{IG_USER_ID}/media",
        data={
            "image_url": image_url,
            "caption": caption,
            "access_token": IG_ACCESS_TOKEN,
        },
        timeout=120,
    )
    print("create_media_container:", response.status_code, response.text)
    response.raise_for_status()
    return response.json()["id"]


def get_container_status(creation_id):
    response = requests.get(
        f"https://graph.facebook.com/v25.0/{creation_id}",
        params={
            "fields": "id,status_code",
            "access_token": IG_ACCESS_TOKEN,
        },
        timeout=60,
    )
    print("get_container_status:", response.status_code, response.text)
    response.raise_for_status()
    return response.json()


def wait_until_media_ready(creation_id, max_attempts=12, delay_seconds=4):
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
        f"https://graph.facebook.com/v25.0/{IG_USER_ID}/media_publish",
        data={
            "creation_id": creation_id,
            "access_token": IG_ACCESS_TOKEN,
        },
        timeout=120,
    )
    print("publish_media_container:", response.status_code, response.text)
    response.raise_for_status()
    return response.json()


# =============================
# CAPTIONS
# =============================
def sanitize_hashtag(text):
    cleaned = "".join(ch for ch in str(text or "") if ch.isalnum())
    return cleaned


def build_alert_caption(league_key, home_team, away_team, minute, score, pick_text):
    hashtags = [
        f"#{sanitize_hashtag(home_team)}",
        f"#{sanitize_hashtag(away_team)}",
        "#FootballAlerts",
        "#LiveAlerts",
        "#FootballPredictions",
        "#BettingTips",
        "#NVMProSystem",
    ]

    return f"""NVM LIVE ALERT

{league_key}
{home_team} vs {away_team}

Minute: {minute}
Score: {score}
Pick: {pick_text}

📲 @nvm_access_engine_bot

{" ".join(hashtags)}
""".strip()


def build_report_caption(title, date_text, wins, lost, winrate, caption_message=""):
    base = f"""{title}

{date_text}

Wins: {wins}
Lost: {lost}
Win Rate: {winrate}

📲 @nvm_access_engine_bot

#FootballAlerts #LiveAlerts #BettingTips #FootballPredictions #NVMProSystem
""".strip()

    extra = str(caption_message or "").strip()
    if extra:
        return f"{base}\n\n{extra}"
    return base


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

        league_key = str(data.get("league_key", "")).strip() or "Live Football"
        home_team = str(data.get("home_team", "")).strip() or "Home"
        away_team = str(data.get("away_team", "")).strip() or "Away"
        minute = str(data.get("minute", "")).strip() or "00"
        score = str(data.get("score", "")).strip() or "0 - 0"
        pick_text = str(data.get("pick_text", "")).strip() or "Over 0.5 Goals"

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

        title = str(data.get("title", "NVM DAILY REPORT")).strip()
        date_text = str(data.get("date_text", "")).strip() or "01/01/2026"
        wins = str(data.get("wins", "0")).strip()
        lost = str(data.get("lost", "0")).strip()
        winrate = str(data.get("winrate", "0%")).strip()
        caption_message = str(data.get("caption_message", "")).strip()

        image_path = build_report_image(
            title=title,
            date_text=date_text,
            wins=wins,
            lost=lost,
            winrate=winrate,
        )

        image_url = upload_to_imgbb(image_path)
        caption = build_report_caption(
            title=title,
            date_text=date_text,
            wins=wins,
            lost=lost,
            winrate=winrate,
            caption_message=caption_message,
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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
