import os
import time
import textwrap
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
def get_font(size: int, bold: bool = False):
    if bold:
        candidates = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
        ]
    else:
        candidates = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
        ]

    for path in candidates:
        if os.path.exists(path):
            try:
                print(f"[FONT] Using: {path} | size={size} | bold={bold}")
                return ImageFont.truetype(path, size=size)
            except Exception as e:
                print(f"[FONT] Failed {path}: {e}")

    print(f"[FONT] Falling back to default font | size={size} | bold={bold}")
    return ImageFont.load_default()

# ================================
# DRAW HELPERS
# ================================
def draw_text_center(
    draw,
    xy,
    text,
    font,
    fill,
    shadow_fill=(0, 0, 0),
    shadow_offset=3,
    stroke_width=2,
    stroke_fill=(0, 0, 0),
    anchor="mm",
):
    x, y = xy
    draw.text(
        (x + shadow_offset, y + shadow_offset),
        text,
        font=font,
        fill=shadow_fill,
        anchor=anchor,
        stroke_width=stroke_width,
        stroke_fill=shadow_fill,
    )
    draw.text(
        (x, y),
        text,
        font=font,
        fill=fill,
        anchor=anchor,
        stroke_width=stroke_width,
        stroke_fill=stroke_fill,
    )

def draw_text_left(
    draw,
    xy,
    text,
    font,
    fill,
    shadow_fill=(0, 0, 0),
    shadow_offset=3,
    stroke_width=2,
    stroke_fill=(0, 0, 0),
    anchor="la",
):
    x, y = xy
    draw.text(
        (x + shadow_offset, y + shadow_offset),
        text,
        font=font,
        fill=shadow_fill,
        anchor=anchor,
        stroke_width=stroke_width,
        stroke_fill=shadow_fill,
    )
    draw.text(
        (x, y),
        text,
        font=font,
        fill=fill,
        anchor=anchor,
        stroke_width=stroke_width,
        stroke_fill=stroke_fill,
    )

def wrap_text_by_pixels(draw, text, font, max_width):
    words = str(text or "").split()
    if not words:
        return [""]

    lines = []
    current = words[0]

    for word in words[1:]:
        test = current + " " + word
        bbox = draw.textbbox((0, 0), test, font=font)
        width = bbox[2] - bbox[0]
        if width <= max_width:
            current = test
        else:
            lines.append(current)
            current = word

    lines.append(current)
    return lines

# ================================
# IMAGE BUILD
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
    soft_white = (245, 245, 245)
    black = (0, 0, 0)

    # FONTURI FOARTE MARI
    font_title = get_font(680, True)
    font_league = get_font(460, True)
    font_match = get_font(580, True)
    font_label = get_font(520, True)
    font_value = get_font(600, True)
    font_pick = get_font(540, True)

    # TITLE
    draw_text_center(
        draw,
        (540, 58),
        "NVM LIVE ALERT",
        font=font_title,
        fill=gold,
        stroke_width=3,
        stroke_fill=black,
    )

    # LEAGUE (wrap pe 2 linii daca e nevoie)
    league_lines = wrap_text_by_pixels(draw, league, font_league, 760)
    league_y = 150
    for i, line in enumerate(league_lines[:2]):
        draw_text_center(
            draw,
            (540, league_y + i * 52),
            line,
            font=font_league,
            fill=soft_white,
            stroke_width=2,
            stroke_fill=black,
        )

    # MATCH
    match_text = f"{home} vs {away}"
    match_lines = wrap_text_by_pixels(draw, match_text, font_match, 860)
    match_y = 250
    for i, line in enumerate(match_lines[:2]):
        draw_text_center(
            draw,
            (540, match_y + i * 64),
            line,
            font=font_match,
            fill=white,
            stroke_width=3,
            stroke_fill=black,
        )

    # ZONA INFO MAI BINE ARANJATA
    x_label = 95
    x_value = 390
    y_start = 430
    row_gap = 125

    # MINUTE
    draw_text_left(
        draw,
        (x_label, y_start),
        "MINUTE:",
        font=font_label,
        fill=gold,
        stroke_width=2,
        stroke_fill=black,
    )
    draw_text_left(
        draw,
        (x_value, y_start),
        str(minute),
        font=font_value,
        fill=white,
        stroke_width=3,
        stroke_fill=black,
    )

    # SCORE
    draw_text_left(
        draw,
        (x_label, y_start + row_gap),
        "SCORE:",
        font=font_label,
        fill=gold,
        stroke_width=2,
        stroke_fill=black,
    )
    draw_text_left(
        draw,
        (x_value, y_start + row_gap),
        str(score),
        font=font_value,
        fill=white,
        stroke_width=3,
        stroke_fill=black,
    )

    # PICK
    draw_text_left(
        draw,
        (x_label, y_start + row_gap * 2),
        "PICK:",
        font=font_label,
        fill=gold,
        stroke_width=2,
        stroke_fill=black,
    )

    pick_lines = wrap_text_by_pixels(draw, str(pick), font_pick, 420)
    pick_base_y = y_start + row_gap * 2
    for i, line in enumerate(pick_lines[:2]):
        draw_text_left(
            draw,
            (x_value, pick_base_y + i * 58),
            line,
            font=font_pick,
            fill=white,
            stroke_width=3,
            stroke_fill=black,
        )

    filename = f"/tmp/alert_{int(time.time())}.jpg"
    img.convert("RGB").save(filename, "JPEG", quality=95)
    print(f"[IMAGE] Saved preview to {filename}")
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
        return {"error": "create_media_error", "details": create_response}

    creation_id = create_response["id"]

    for _ in range(12):
        status_response = requests.get(
            f"{BASE_URL}/{creation_id}",
            params={"fields": "status_code", "access_token": access_token},
            timeout=60
        ).json()

        status_code = str(status_response.get("status_code", "")).upper()

        if status_code == "FINISHED":
            break

        if status_code == "ERROR":
            return {"error": "media_status_error", "details": status_response}

        time.sleep(5)

    publish_url = f"{BASE_URL}/{IG_USER_ID}/media_publish"
    publish_response = requests.post(
        publish_url,
        data={"creation_id": creation_id, "access_token": access_token},
        timeout=120
    ).json()

    return publish_response

# ================================
# ROUTES
# ================================
@app.route("/")
def home():
    return "NVM INSTAGRAM LIVE READY"

@app.route("/meta-login")
def meta_login():
    login_url = (
        f"https://www.facebook.com/v19.0/dialog/oauth"
        f"?client_id={META_APP_ID}"
        f"&redirect_uri={META_REDIRECT_URI}"
        f"&scope=pages_show_list,pages_read_engagement,instagram_basic,instagram_content_publish"
    )
    return redirect(login_url)

@app.route("/meta-callback")
def meta_callback():
    code = request.args.get("code")
    if not code:
        return jsonify({"ok": False, "error": "No code received"}), 400

    token_url = (
        f"{BASE_URL}/oauth/access_token"
        f"?client_id={META_APP_ID}"
        f"&redirect_uri={META_REDIRECT_URI}"
        f"&client_secret={META_APP_SECRET}"
        f"&code={code}"
    )

    try:
        response = requests.get(token_url, timeout=60)
        data = response.json()
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

    if "access_token" not in data:
        return jsonify({"ok": False, "details": data}), 400

    access_token = data["access_token"]

    with open(TOKEN_FILE, "w", encoding="utf-8") as f:
        f.write(access_token)

    return jsonify({
        "ok": True,
        "message": "Token generated and saved.",
        "access_token": access_token
    })

@app.route("/get-token")
def get_token():
    if not os.path.exists(TOKEN_FILE):
        return jsonify({"ok": False, "error": "No token saved"}), 404

    with open(TOKEN_FILE, "r", encoding="utf-8") as f:
        token = f.read().strip()

    return jsonify({"ok": True, "token": token})

@app.route("/preview-alert", methods=["POST"])
def preview_alert():
    try:
        data = request.get_json(force=True) or {}

        league = data.get("league", data.get("league_key", ""))
        home = data.get("home", data.get("home_team", ""))
        away = data.get("away", data.get("away_team", ""))
        minute = data.get("minute", "")
        score = data.get("score", "")
        pick = data.get("pick", data.get("pick_text", ""))

        image_path = build_image(league, home, away, minute, score, pick)
        image_url = upload_image(image_path)

        return jsonify({
            "ok": True,
            "preview_only": True,
            "image_url": image_url
        })
    except Exception as e:
        return jsonify({
            "ok": False,
            "error": str(e)
        }), 500

@app.route("/post-alert", methods=["POST"])
def post_alert():
    try:
        data = request.get_json(force=True) or {}

        league = data.get("league", data.get("league_key", ""))
        home = data.get("home", data.get("home_team", ""))
        away = data.get("away", data.get("away_team", ""))
        minute = data.get("minute", "")
        score = data.get("score", "")
        pick = data.get("pick", data.get("pick_text", ""))
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
