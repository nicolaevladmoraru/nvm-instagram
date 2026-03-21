import os
import time
from flask import Flask, request, jsonify, send_file, abort, make_response
import requests
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GENERATED_DIR = os.path.join(BASE_DIR, "generated_media")

os.makedirs(GENERATED_DIR, exist_ok=True)

app = Flask(__name__)

IG_ACCESS_TOKEN = (os.getenv("IG_ACCESS_TOKEN") or "").strip()
IG_USER_ID = (os.getenv("IG_USER_ID") or "").strip()


# =============================
# IMAGE SAVE
# =============================
def save_image(img, name):
    filename = f"{name}_{int(time.time())}.jpg"
    path = os.path.join(GENERATED_DIR, filename)

    rgb_img = img.convert("RGB")
    rgb_img.save(path, "JPEG", quality=95, optimize=True)

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
# PUBLIC IMAGE ROUTE
# =============================
@app.route("/media/<filename>")
def media_file(filename):
    safe_name = os.path.basename(filename)
    path = os.path.join(GENERATED_DIR, safe_name)

    if not os.path.exists(path):
        abort(404)

    response = make_response(send_file(path, mimetype="image/jpeg", conditional=False))
    response.headers["Content-Type"] = "image/jpeg"
    response.headers["Cache-Control"] = "public, max-age=86400"
    response.headers["Content-Disposition"] = f'inline; filename="{safe_name}"'
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


# =============================
# IMAGE URL HELPERS
# =============================
def build_public_base_url(req) -> str:
    forwarded_proto = (req.headers.get("X-Forwarded-Proto") or "").strip().lower()
    host = (req.headers.get("X-Forwarded-Host") or req.host or "").strip()

    if forwarded_proto == "https" and host:
        return f"https://{host}"

    base_url = req.url_root.rstrip("/")
    if base_url.startswith("http://"):
        base_url = "https://" + base_url[len("http://"):]
    return base_url


def verify_public_image(image_url: str) -> None:
    test_resp = requests.get(
        image_url,
        timeout=30,
        headers={"User-Agent": "Mozilla/5.0"},
        allow_redirects=True,
    )

    content_type = str(test_resp.headers.get("Content-Type") or "").lower()
    content_len = len(test_resp.content or b"")

    print("verify_public_image status:", test_resp.status_code)
    print("verify_public_image content-type:", content_type)
    print("verify_public_image content-length:", content_len)
    print("verify_public_image final-url:", test_resp.url)

    if test_resp.status_code != 200:
        raise RuntimeError(f"Public image URL is not reachable: {test_resp.status_code}")

    if "image/jpeg" not in content_type and "image/jpg" not in content_type:
        raise RuntimeError(f"Public image URL is not JPEG. Content-Type={content_type}")

    if content_len <= 1000:
        raise RuntimeError("Public image content looks too small or invalid.")


# =============================
# INSTAGRAM / META HELPERS
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

    if response.status_code != 200:
        raise RuntimeError(
            f"Meta create media error | image_url={image_url} | response={response.text}"
        )

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

    if response.status_code != 200:
        raise RuntimeError(f"Meta status error: {response.text}")

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

    if response.status_code != 200:
        raise RuntimeError(f"Meta publish error: {response.text}")

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
        "ig_user_id": IG_USER_ID,
        "token_length": len(IG_ACCESS_TOKEN),
        "token_prefix": IG_ACCESS_TOKEN[:8] if IG_ACCESS_TOKEN else "",
        "generated_dir": GENERATED_DIR,
    })


@app.route("/post-alert", methods=["POST"])
def post_alert():
    try:
        data = request.get_json(force=True) or {}

        league_key = str(data.get("league_key", "League"))
        home_team = str(data.get("home_team", "Home"))
        away_team = str(data.get("away_team", "Away"))
        minute = str(data.get("minute", "00"))
        score = str(data.get("score", "0 - 0"))
        pick_text = str(data.get("pick_text", "Over 0.5 Goals"))

        image_path, filename = build_alert_image(
            league_key,
            home_team,
            away_team,
            minute,
            score,
            pick_text,
        )

        base_url = build_public_base_url(request)
        image_url = f"{base_url}/media/{filename}"

        print("IMAGE PATH:", image_path)
        print("IMAGE URL:", image_url)

        verify_public_image(image_url)

        caption = build_alert_caption(
            league_key,
            home_team,
            away_team,
            minute,
            score,
            pick_text,
        )

        creation_id = create_media_container(image_url, caption)
        status_result = wait_until_media_ready(creation_id)
        publish_result = publish_media_container(creation_id)

        return jsonify({
            "ok": True,
            "image_path": image_path,
            "image_url": image_url,
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

        title = str(data.get("title", "NVM DAILY REPORT"))
        date_text = str(data.get("date_text", "01/01/2026"))
        wins = str(data.get("wins", "0"))
        lost = str(data.get("lost", "0"))
        winrate = str(data.get("winrate", "0%"))
        caption_message = str(data.get("caption_message", ""))

        image_path, filename = build_report_image(
            title,
            date_text,
            wins,
            lost,
            winrate,
        )

        base_url = build_public_base_url(request)
        image_url = f"{base_url}/media/{filename}"

        print("IMAGE PATH:", image_path)
        print("IMAGE URL:", image_url)

        verify_public_image(image_url)

        caption = build_report_caption(
            title,
            date_text,
            wins,
            lost,
            winrate,
            caption_message,
        )

        creation_id = create_media_container(image_url, caption)
        status_result = wait_until_media_ready(creation_id)
        publish_result = publish_media_container(creation_id)

        return jsonify({
            "ok": True,
            "image_path": image_path,
            "image_url": image_url,
            "creation_id": creation_id,
            "status_result": status_result,
            "publish_result": publish_result,
        })

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
