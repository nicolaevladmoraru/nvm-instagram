import os
import time
import requests
from flask import Flask, request, jsonify, redirect
from PIL import Image, ImageDraw, ImageFont
import cloudinary
import cloudinary.uploader

app = Flask(__name__)

# =============================
# ENV
# =============================
META_APP_ID = os.getenv("META_APP_ID")
META_APP_SECRET = os.getenv("META_APP_SECRET")
META_REDIRECT_URI = os.getenv("META_REDIRECT_URI")

IG_USER_ID = os.getenv("IG_USER_ID")
IG_ACCESS_TOKEN = os.getenv("IG_ACCESS_TOKEN")

# =============================
# CLOUDINARY CONFIG
# =============================
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

# =============================
# TOKEN STORAGE
# =============================
TOKEN_FILE = "/tmp/meta_token.txt"


# =============================
# META LOGIN
# =============================
@app.route("/meta-login")
def meta_login():
    url = (
        f"https://www.facebook.com/v19.0/dialog/oauth"
        f"?client_id={META_APP_ID}"
        f"&redirect_uri={META_REDIRECT_URI}"
        f"&scope=instagram_basic,instagram_content_publish,pages_show_list,pages_read_engagement"
    )
    return redirect(url)


@app.route("/meta-callback")
def meta_callback():
    code = request.args.get("code")

    if not code:
        return "No code"

    url = (
        f"https://graph.facebook.com/v19.0/oauth/access_token"
        f"?client_id={META_APP_ID}"
        f"&redirect_uri={META_REDIRECT_URI}"
        f"&client_secret={META_APP_SECRET}"
        f"&code={code}"
    )

    res = requests.get(url).json()

    if "access_token" not in res:
        return res

    token = res["access_token"]

    with open(TOKEN_FILE, "w") as f:
        f.write(token)

    return {
        "ok": True,
        "access_token": token
    }


@app.route("/get-token")
def get_token():
    if not os.path.exists(TOKEN_FILE):
        return {"error": "no token"}

    with open(TOKEN_FILE) as f:
        return {"token": f.read()}


# =============================
# FONT
# =============================
def get_font(size, bold=False):
    path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    return ImageFont.truetype(path, size)


# =============================
# BUILD IMAGE (TEXT FOARTE MARE)
# =============================
def build_image(league, home, away, minute, score, pick):
    base = Image.open("template.png").convert("RGBA")
    draw = ImageDraw.Draw(base)

    gold = (242, 196, 78)
    white = (255, 255, 255)

    # TEXTURI MARI (cum ai cerut)
    font_title = get_font(120, True)
    font_league = get_font(80, True)
    font_match = get_font(90, True)
    font_label = get_font(70, True)
    font_value = get_font(70, True)

    # TITLE
    draw.text((540, 60), "NVM LIVE ALERT", fill=gold, font=font_title, anchor="mm")

    # LEAGUE
    draw.text((540, 180), league, fill=white, font=font_league, anchor="mm")

    # MATCH
    match = f"{home} vs {away}"
    draw.text((540, 300), match, fill=white, font=font_match, anchor="mm")

    # LABELS
    draw.text((100, 500), "MINUTE:", fill=gold, font=font_label)
    draw.text((100, 600), "SCORE:", fill=gold, font=font_label)
    draw.text((100, 700), "PICK:", fill=gold, font=font_label)

    # VALUES
    draw.text((450, 500), minute, fill=white, font=font_value)
    draw.text((450, 600), score, fill=white, font=font_value)
    draw.text((450, 700), pick, fill=gold, font=font_value)

    path = f"/tmp/alert_{int(time.time())}.jpg"
    base.convert("RGB").save(path, "JPEG", quality=95)

    return path


# =============================
# UPLOAD CLOUDINARY
# =============================
def upload_image(path):
    res = cloudinary.uploader.upload(path, folder="nvm_instagram")
    return res["secure_url"]


# =============================
# INSTAGRAM POST
# =============================
def post_instagram(image_url, caption):
    url = f"https://graph.facebook.com/v19.0/{IG_USER_ID}/media"

    data = {
        "image_url": image_url,
        "caption": caption,
        "access_token": IG_ACCESS_TOKEN
    }

    r = requests.post(url, data=data)
    if r.status_code != 200:
        return r.text

    creation_id = r.json()["id"]

    publish = requests.post(
        f"https://graph.facebook.com/v19.0/{IG_USER_ID}/media_publish",
        data={
            "creation_id": creation_id,
            "access_token": IG_ACCESS_TOKEN
        }
    )

    return publish.json()


# =============================
# POST ALERT
# =============================
@app.route("/post-alert", methods=["POST"])
def post_alert():
    data = request.get_json()

    league = data.get("league", "")
    home = data.get("home", "")
    away = data.get("away", "")
    minute = data.get("minute", "")
    score = data.get("score", "")
    pick = data.get("pick", "")

    img = build_image(league, home, away, minute, score, pick)
    url = upload_image(img)

    caption = f"{league}\n{home} vs {away}\nMinute {minute}\nScore {score}\nPick: {pick}"

    result = post_instagram(url, caption)

    return {
        "ok": True,
        "image_url": url,
        "result": result
    }


# =============================
@app.route("/")
def home():
    return "NVM INSTAGRAM LIVE READY"
