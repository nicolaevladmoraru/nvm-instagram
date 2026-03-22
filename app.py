import os
import time
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
def get_matplotlib_font_path(bold: bool = False):
    try:
        import matplotlib.font_manager as fm

        preferred = [
            "DejaVu Sans",
            "Liberation Sans",
            "Arial",
            "sans-serif",
        ]

        for family in preferred:
            try:
                props = fm.FontProperties(
                    family=family,
                    weight="bold" if bold else "normal"
                )
                path = fm.findfont(props, fallback_to_default=True)
                if path and os.path.exists(path):
                    print(f"[FONT] Matplotlib font found: {path} | bold={bold}")
                    return path
            except Exception as e:
                print(f"[FONT] Matplotlib lookup failed for {family}: {e}")

    except Exception as e:
        print(f"[FONT] Matplotlib not available: {e}")

    return None


def get_truetype_font(size: int, bold: bool = False):
    local_candidates = []

    if bold:
        local_candidates = [
            "DejaVuSans-Bold.ttf",
            "DejaVuSans.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
        ]
    else:
        local_candidates = [
            "DejaVuSans.ttf",
            "DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
        ]

    # 1) normal paths / filenames
    for candidate in local_candidates:
        try:
            font = ImageFont.truetype(candidate, size=size)
            print(f"[FONT] Using local: {candidate} | size={size} | bold={bold}")
            return font
        except Exception as e:
            print(f"[FONT] Failed local: {candidate} | {e}")

    # 2) matplotlib bundled fonts
    mpl_path = get_matplotlib_font_path(bold=bold)
    if mpl_path:
        try:
            font = ImageFont.truetype(mpl_path, size=size)
            print(f"[FONT] Using matplotlib: {mpl_path} | size={size} | bold={bold}")
            return font
        except Exception as e:
            print(f"[FONT] Failed matplotlib font: {mpl_path} | {e}")

    print(f"[FONT] No truetype font found | size={size} | bold={bold}")
    return None

# ================================
# TEXT HELPERS
# ================================
def text_size(draw: ImageDraw.ImageDraw, text: str, font) -> tuple[int, int]:
    bbox = draw.textbbox((0, 0), str(text), font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def wrap_text_by_pixels(draw: ImageDraw.ImageDraw, text: str, font, max_width: int):
    words = str(text or "").split()
    if not words:
        return [""]

    lines = []
    current = words[0]

    for word in words[1:]:
        test = current + " " + word
        w, _ = text_size(draw, test, font)
        if w <= max_width:
            current = test
        else:
            lines.append(current)
            current = word

    lines.append(current)
    return lines


def draw_scaled_bitmap_text(
    base_img: Image.Image,
    x: int,
    y: int,
    text: str,
    target_height: int,
    fill=(255, 255, 255),
    stroke_fill=(0, 0, 0),
    anchor: str = "lt",
):
    default_font = ImageFont.load_default()

    temp_img = Image.new("RGBA", (4000, 1200), (0, 0, 0, 0))
    temp_draw = ImageDraw.Draw(temp_img)

    stroke_offsets = [
        (-3, -3), (-3, 0), (-3, 3),
        (0, -3),           (0, 3),
        (3, -3),  (3, 0),  (3, 3),
    ]

    for dx, dy in stroke_offsets:
        temp_draw.text((30 + dx, 30 + dy), str(text), font=default_font, fill=stroke_fill)

    temp_draw.text((30, 30), str(text), font=default_font, fill=fill)

    bbox = temp_img.getbbox()
    if not bbox:
        return

    cropped = temp_img.crop(bbox)
    cw, ch = cropped.size
    if ch <= 0:
        return

    scale = max(1, int(target_height / ch))
    # smoother than NEAREST
    enlarged = cropped.resize((cw * scale, ch * scale), Image.Resampling.BICUBIC)

    ew, eh = enlarged.size

    if anchor == "mm":
        px = int(x - ew / 2)
        py = int(y - eh / 2)
    elif anchor == "lm":
        px = int(x)
        py = int(y - eh / 2)
    else:
        px = int(x)
        py = int(y)

    base_img.alpha_composite(enlarged, (px, py))


def draw_text(
    base_img: Image.Image,
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    text: str,
    size: int,
    fill=(255, 255, 255),
    stroke_fill=(0, 0, 0),
    bold: bool = True,
    anchor: str = "lt",
    fallback_height: int | None = None,
):
    font = get_truetype_font(size=size, bold=bold)

    if font is not None:
        draw.text(
            (x, y),
            str(text),
            fill=fill,
            anchor=anchor,
            font=font,
            stroke_width=max(2, int(size * 0.06)),
            stroke_fill=stroke_fill,
        )
        return font

    draw_scaled_bitmap_text(
        base_img=base_img,
        x=x,
        y=y,
        text=text,
        target_height=fallback_height or size,
        fill=fill,
        stroke_fill=stroke_fill,
        anchor=anchor,
    )
    return ImageFont.load_default()

# ================================
# IMAGE BUILD
# ================================
def build_image(league, home, away, minute, score, pick):
    template_path = "template.png"

    if os.path.exists(template_path):
        img = Image.open(template_path).convert("RGBA")
    else:
        img = Image.new("RGBA", (1024, 1024), (10, 15, 35, 255))

    draw = ImageDraw.Draw(img)
    w, h = img.size
    print(f"[IMAGE] template_size={img.size}")

    gold = (242, 196, 78)
    white = (255, 255, 255)
    black = (0, 0, 0)

    center_x = int(w * 0.50)

    # sizes
    title_size = int(h * 0.040)
    league_size = int(h * 0.052)
    match_size = int(h * 0.060)
    label_size = int(h * 0.060)
    value_size = int(h * 0.072)
    pick_size = int(h * 0.060)

    # fallback heights
    title_fallback_h = int(h * 0.040)
    league_fallback_h = int(h * 0.055)
    match_fallback_h = int(h * 0.070)
    label_fallback_h = int(h * 0.060)
    value_fallback_h = int(h * 0.075)
    pick_fallback_h = int(h * 0.065)

    # title
    draw_text(
        base_img=img,
        draw=draw,
        x=center_x,
        y=int(h * 0.06),
        text="NVM LIVE ALERT",
        size=title_size,
        fill=gold,
        stroke_fill=black,
        bold=True,
        anchor="mm",
        fallback_height=title_fallback_h,
    )

    # wrap font
    wrap_font = get_truetype_font(max(22, int(h * 0.035)), bold=True) or ImageFont.load_default()

    # league
    league_lines = wrap_text_by_pixels(draw, str(league), wrap_font, int(w * 0.72))
    league_y = int(h * 0.16)
    for i, line in enumerate(league_lines[:2]):
        draw_text(
            base_img=img,
            draw=draw,
            x=center_x,
            y=league_y + i * int(h * 0.055),
            text=line,
            size=league_size,
            fill=white,
            stroke_fill=black,
            bold=True,
            anchor="mm",
            fallback_height=league_fallback_h,
        )

    # match
    match_text = f"{home} vs {away}"
    match_lines = wrap_text_by_pixels(draw, match_text, wrap_font, int(w * 0.80))
    match_y = int(h * 0.27)
    for i, line in enumerate(match_lines[:2]):
        draw_text(
            base_img=img,
            draw=draw,
            x=center_x,
            y=match_y + i * int(h * 0.065),
            text=line,
            size=match_size,
            fill=white,
            stroke_fill=black,
            bold=True,
            anchor="mm",
            fallback_height=match_fallback_h,
        )

    # left info block
    x_label = int(w * 0.08)
    x_value = int(w * 0.35)
    y_start = int(h * 0.41)
    row_gap = int(h * 0.115)

    # minute
    draw_text(
        base_img=img,
        draw=draw,
        x=x_label,
        y=y_start,
        text="MINUTE:",
        size=label_size,
        fill=gold,
        stroke_fill=black,
        bold=True,
        anchor="lt",
        fallback_height=label_fallback_h,
    )
    draw_text(
        base_img=img,
        draw=draw,
        x=x_value,
        y=y_start,
        text=str(minute),
        size=value_size,
        fill=white,
        stroke_fill=black,
        bold=True,
        anchor="lt",
        fallback_height=value_fallback_h,
    )

    # score
    draw_text(
        base_img=img,
        draw=draw,
        x=x_label,
        y=y_start + row_gap,
        text="SCORE:",
        size=label_size,
        fill=gold,
        stroke_fill=black,
        bold=True,
        anchor="lt",
        fallback_height=label_fallback_h,
    )
    draw_text(
        base_img=img,
        draw=draw,
        x=x_value,
        y=y_start + row_gap,
        text=str(score),
        size=value_size,
        fill=white,
        stroke_fill=black,
        bold=True,
        anchor="lt",
        fallback_height=value_fallback_h,
    )

    # pick
    draw_text(
        base_img=img,
        draw=draw,
        x=x_label,
        y=y_start + row_gap * 2,
        text="PICK",
        size=label_size,
        fill=gold,
        stroke_fill=black,
        bold=True,
        anchor="lt",
        fallback_height=label_fallback_h,
    )

    pick_wrap_font = get_truetype_font(max(20, int(h * 0.033)), bold=True) or ImageFont.load_default()
    pick_lines = wrap_text_by_pixels(draw, str(pick), pick_wrap_font, int(w * 0.36))
    for i, line in enumerate(pick_lines[:2]):
        draw_text(
            base_img=img,
            draw=draw,
            x=x_value,
            y=y_start + row_gap * 2 + i * int(h * 0.060),
            text=line,
            size=pick_size,
            fill=white,
            stroke_fill=black,
            bold=True,
            anchor="lt",
            fallback_height=pick_fallback_h,
        )

    filename = f"/tmp/alert_{int(time.time())}.jpg"
    img.convert("RGB").save(filename, "JPEG", quality=95)
    print(f"[IMAGE] Saved preview to {filename} | final_size={img.size}")
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
            params={
                "fields": "status_code",
                "access_token": access_token
            },
            timeout=60
        ).json()

        status_code = str(status_response.get("status_code", "")).upper()

        if status_code == "FINISHED":
            break

        if status_code == "ERROR":
            return {"error": "media_status_error", "details": status_response}

        time.sleep(5)

    publish_url = f"{BASE_URL}/{IG_USER_ID}/media_publish"
    publish_payload = {
        "creation_id": creation_id,
        "access_token": access_token
    }

    publish_response = requests.post(publish_url, data=publish_payload, timeout=120).json()
    return publish_response

# ================================
# META LOGIN
# ================================
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

# ================================
# ROUTES
# ================================
@app.route("/")
def home():
    return "NVM INSTAGRAM LIVE READY"

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
