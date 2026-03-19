import os
import re
import time
import textwrap
import tempfile
from pathlib import Path

import requests
from flask import Flask, request, jsonify
from PIL import Image, ImageDraw, ImageFont

app = Flask(__name__)

IG_USER_ID = (os.getenv("IG_USER_ID") or "").strip()
IG_ACCESS_TOKEN = (os.getenv("IG_ACCESS_TOKEN") or "").strip()
IMGBB_API_KEY = (os.getenv("IMGBB_API_KEY") or "").strip()

GRAPH_INSTAGRAM_BASE = "https://graph.instagram.com"

TMP_DIR = Path(tempfile.gettempdir()) / "nvm_instagram"
TMP_DIR.mkdir(parents=True, exist_ok=True)


# =========================================================
# HELPERS
# =========================================================
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
        if Path(path).exists():
            return ImageFont.truetype(path, size=size)

    return ImageFont.load_default()


def wrap_text(text: str, width: int) -> list[str]:
    return textwrap.wrap(text, width=width) if text else []


def save_image(img: Image.Image, prefix: str) -> str:
    filename = TMP_DIR / f"{prefix}_{int(time.time() * 1000)}.jpg"
    img.save(filename, format="JPEG", quality=95)
    return str(filename)


def sanitize_hashtag(text: str) -> str:
    text = re.sub(r"[^A-Za-z0-9]+", "", str(text or ""))
    return text


def league_to_hashtags(league_key: str) -> list[str]:
    base = []
    cleaned = str(league_key or "").strip()

    if not cleaned:
        return base

    parts = [p.strip() for p in cleaned.split("-") if p.strip()]
    for part in parts:
        tag = sanitize_hashtag(part)
        if tag:
            base.append(f"#{tag}")

    merged = sanitize_hashtag(cleaned)
    if merged:
        base.append(f"#{merged}")

    lower = cleaned.lower()
    if "premier league" in lower:
        base.extend(["#PremierLeague", "#EPL"])
    elif "la liga" in lower:
        base.extend(["#LaLiga"])
    elif "serie a" in lower:
        base.extend(["#SerieA"])
    elif "bundesliga" in lower:
        base.extend(["#Bundesliga"])
    elif "ligue 1" in lower:
        base.extend(["#Ligue1"])
    elif "championship" in lower:
        base.extend(["#Championship"])

    return list(dict.fromkeys(base))


def team_to_hashtags(team: str) -> list[str]:
    raw = str(team or "").strip()
    if not raw:
        return []

    compact = sanitize_hashtag(raw)
    words = [sanitize_hashtag(x) for x in raw.split() if sanitize_hashtag(x)]

    tags = []
    if compact:
        tags.append(f"#{compact}")
    for word in words:
        tags.append(f"#{word}")

    return list(dict.fromkeys(tags))


def build_alert_caption(
    league_key: str,
    home_team: str,
    away_team: str,
    minute: str,
    score: str,
    pick_text: str,
) -> str:
    title = f"{league_key} | {home_team} vs {away_team}".strip(" |")

    description_lines = [
        title,
        "",
        "⚽ Live Alert",
        f"⏱ Minute: {minute}",
        f"📊 Score: {score}",
        f"🔥 Pick: {pick_text}",
        "",
        "📲 Join now on Telegram:",
        "@nvm_access_engine_bot",
        "",
    ]

    hashtags = []
    hashtags.extend(league_to_hashtags(league_key))
    hashtags.extend(team_to_hashtags(home_team))
    hashtags.extend(team_to_hashtags(away_team))
    hashtags.extend([
        "#FootballAlerts",
        "#LiveBetting",
        "#BettingTips",
        "#FootballPredictions",
        "#SoccerTips",
        "#GoalAlert",
        "#LiveAlerts",
        "#NVMProSystem",
    ])

    hashtags = list(dict.fromkeys(hashtags))
    description_lines.append(" ".join(hashtags[:18]))

    return "\n".join(description_lines).strip()


def build_report_caption(title: str, period_label: str) -> str:
    return (
        f"{title}\n"
        f"📅 {period_label}\n\n"
        "📲 Join now on Telegram:\n"
        "@nvm_access_engine_bot\n\n"
        "#FootballAlerts #LiveAlerts #BettingTips #FootballPredictions "
        "#SoccerTips #NVMProSystem"
    )


def post_image_to_imgbb(local_path: str) -> str:
    if not IMGBB_API_KEY:
        raise RuntimeError("Missing IMGBB_API_KEY")

    with open(local_path, "rb") as f:
        response = requests.post(
            "https://api.imgbb.com/1/upload",
            params={"key": IMGBB_API_KEY},
            files={"image": f},
            timeout=120,
        )
    response.raise_for_status()
    data = response.json()

    if not data.get("success"):
        raise RuntimeError(f"imgbb upload failed: {data}")

    return data["data"]["url"]


def create_media_container(image_url: str, caption: str) -> str:
    url = f"{GRAPH_INSTAGRAM_BASE}/{IG_USER_ID}/media"
    payload = {
        "image_url": image_url,
        "caption": caption,
        "access_token": IG_ACCESS_TOKEN,
    }
    response = requests.post(url, data=payload, timeout=120)
    response.raise_for_status()
    return response.json()["id"]


def get_container_status(creation_id: str) -> dict:
    url = f"{GRAPH_INSTAGRAM_BASE}/{creation_id}"
    params = {
        "fields": "id,status_code",
        "access_token": IG_ACCESS_TOKEN,
    }
    response = requests.get(url, params=params, timeout=60)
    response.raise_for_status()
    return response.json()


def wait_until_media_ready(creation_id: str, max_attempts: int = 10, delay_seconds: int = 4) -> dict:
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


def publish_media_container(creation_id: str) -> dict:
    url = f"{GRAPH_INSTAGRAM_BASE}/{IG_USER_ID}/media_publish"
    payload = {
        "creation_id": creation_id,
        "access_token": IG_ACCESS_TOKEN,
    }
    response = requests.post(url, data=payload, timeout=120)
    response.raise_for_status()
    return response.json()


# =========================================================
# IMAGE BUILDERS
# =========================================================
def build_alert_image(
    league_key: str,
    home_team: str,
    away_team: str,
    minute: str,
    score: str,
    pick_text: str,
) -> str:
    width, height = 1080, 1080
    img = Image.new("RGB", (width, height), (11, 20, 39))
    draw = ImageDraw.Draw(img)

    gold = (242, 196, 78)
    white = (245, 247, 250)
    blue = (70, 130, 220)
    gray = (182, 190, 200)
    green = (135, 245, 150)

    font_title = get_font(60, bold=True)
    font_match = get_font(52, bold=True)
    font_label = get_font(34, bold=True)
    font_value = get_font(48, bold=True)
    font_pick = get_font(58, bold=True)
    font_small = get_font(28, bold=False)

    draw.rounded_rectangle((36, 36, 1044, 1044), radius=34, outline=blue, width=4)

    # Faint background branding on right side
    draw.ellipse((650, 170, 1040, 560), outline=(40, 70, 130), width=6)
    draw.text((760, 305), "NVM", font=get_font(88, bold=True), fill=(34, 55, 92))

    draw.text((60, 70), "NVM LIVE ALERTS", font=font_title, fill=gold)

    y = 175
    for line in wrap_text(league_key, 28):
        draw.text((60, y), line, font=font_small, fill=gray)
        y += 34

    y += 20
    for line in wrap_text(f"{home_team} vs {away_team}", 24):
        draw.text((60, y), line, font=font_match, fill=white)
        y += 62

    # Center block
    center_x = width // 2
    y = 450

    draw.text((center_x - 90, y), "MINUTE", font=font_label, fill=gray)
    y += 40
    minute_bbox = draw.textbbox((0, 0), minute, font=font_value)
    minute_w = minute_bbox[2] - minute_bbox[0]
    draw.text((center_x - minute_w / 2, y), minute, font=font_value, fill=white)

    y += 110
    draw.text((center_x - 65, y), "SCORE", font=font_label, fill=gray)
    y += 40
    score_bbox = draw.textbbox((0, 0), score, font=font_value)
    score_w = score_bbox[2] - score_bbox[0]
    draw.text((center_x - score_w / 2, y), score, font=font_value, fill=white)

    y += 110
    draw.text((center_x - 45, y), "PICK", font=font_label, fill=gray)
    y += 44
    for line in wrap_text(pick_text.upper(), 18):
        line_bbox = draw.textbbox((0, 0), line, font=font_pick)
        line_w = line_bbox[2] - line_bbox[0]
        draw.text((center_x - line_w / 2, y), line, font=font_pick, fill=green)
        y += 66

    # Bottom CTA
    cta_y = 900
    draw.text((60, cta_y), "Join now on Telegram", font=get_font(34, bold=True), fill=gold)
    draw.text((60, cta_y + 44), "@nvm_access_engine_bot", font=get_font(32, bold=False), fill=white)

    return save_image(img, "alert")


def build_report_image(title: str, period_label: str, message: str) -> str:
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

    draw.text((60, 60), title, font=font_title, fill=gold)
    draw.text((60, 138), period_label, font=font_sub, fill=gray)

    y = 220
    for paragraph in str(message or "").split("\n"):
        paragraph = paragraph.strip()
        if paragraph == "":
            y += 16
            continue

        wrapped = wrap_text(paragraph, 48)
        for line in wrapped:
            draw.text((60, y), line, font=font_text, fill=white)
            y += 38

        y += 4
        if y > 1180:
            break

    draw.text((60, 1240), "Join now on Telegram", font=get_font(34, bold=True), fill=gold)
    draw.text((60, 1284), "@nvm_access_engine_bot", font=font_small, fill=white)

    return save_image(img, "report")


# =========================================================
# ROUTES
# =========================================================
@app.route("/", methods=["GET"])
def home():
    return "nvm-instagram running"


@app.route("/debug-env", methods=["GET"])
def debug_env():
    token = IG_ACCESS_TOKEN or ""
    return jsonify({
        "ig_user_id": IG_USER_ID,
        "token_prefix": token[:8],
        "token_length": len(token),
        "has_imgbb": bool(IMGBB_API_KEY),
    })


@app.route("/debug-me", methods=["GET"])
def debug_me():
    try:
        url = f"{GRAPH_INSTAGRAM_BASE}/me"
        params = {
            "fields": "id,username",
            "access_token": IG_ACCESS_TOKEN,
        }
        response = requests.get(url, params=params, timeout=60)
        response.raise_for_status()
        return jsonify({"ok": True, "me": response.json()})
    except requests.HTTPError as e:
        try:
            details = e.response.json()
        except Exception:
            details = e.response.text
        return jsonify({"ok": False, "error": "Meta API error", "details": details}), 500
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/post-alert", methods=["POST"])
def post_alert():
    try:
        data = request.get_json(force=True)

        league_key = str(data.get("league_key", "")).strip()
        home_team = str(data.get("home_team", "Home")).strip()
        away_team = str(data.get("away_team", "Away")).strip()
        minute = str(data.get("minute", "00")).strip()
        score = str(data.get("score", "0 - 0")).strip()
        pick_text = str(data.get("pick_text", "")).strip()

        if not IG_USER_ID or not IG_ACCESS_TOKEN:
            return jsonify({"ok": False, "error": "Missing IG_USER_ID or IG_ACCESS_TOKEN"}), 500

        local_path = build_alert_image(
            league_key=league_key,
            home_team=home_team,
            away_team=away_team,
            minute=minute,
            score=score,
            pick_text=pick_text,
        )

        public_image_url = post_image_to_imgbb(local_path)

        caption = build_alert_caption(
            league_key=league_key,
            home_team=home_team,
            away_team=away_team,
            minute=minute,
            score=score,
            pick_text=pick_text,
        )

        creation_id = create_media_container(public_image_url, caption)
        status_result = wait_until_media_ready(creation_id)
        publish_result = publish_media_container(creation_id)

        return jsonify({
            "ok": True,
            "image_url": public_image_url,
            "caption": caption,
            "creation_id": creation_id,
            "status_result": status_result,
            "publish_result": publish_result,
        })

    except requests.HTTPError as e:
        try:
            details = e.response.json()
        except Exception:
            details = e.response.text
        return jsonify({"ok": False, "error": "Meta API error", "details": details}), 500
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/post-report", methods=["POST"])
def post_report():
    try:
        data = request.get_json(force=True)

        title = str(data.get("title", "NVM LIVE ALERTS DAILY REPORT")).strip()
        period_label = str(data.get("period_label", "")).strip()
        message = str(data.get("message", "")).strip()

        if not IG_USER_ID or not IG_ACCESS_TOKEN:
            return jsonify({"ok": False, "error": "Missing IG_USER_ID or IG_ACCESS_TOKEN"}), 500

        if not message:
            return jsonify({"ok": False, "error": "message is required"}), 400

        local_path = build_report_image(
            title=title,
            period_label=period_label,
            message=message,
        )

        public_image_url = post_image_to_imgbb(local_path)
        caption = build_report_caption(title, period_label)

        creation_id = create_media_container(public_image_url, caption)
        status_result = wait_until_media_ready(creation_id)
        publish_result = publish_media_container(creation_id)

        return jsonify({
            "ok": True,
            "image_url": public_image_url,
            "caption": caption,
            "creation_id": creation_id,
            "status_result": status_result,
            "publish_result": publish_result,
        })

    except requests.HTTPError as e:
        try:
            details = e.response.json()
        except Exception:
            details = e.response.text
        return jsonify({"ok": False, "error": "Meta API error", "details": details}), 500
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
