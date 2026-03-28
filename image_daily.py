import os
import time
from PIL import Image, ImageDraw

from font_utils import draw_text

TEMPLATE_PATH = "templates/template_daily_report.png"


def build_daily_report(date_text, wins, lost, winrate):
    if os.path.exists(TEMPLATE_PATH):
        img = Image.open(TEMPLATE_PATH).convert("RGBA")
    else:
        img = Image.new("RGBA", (1024, 1024), (10, 15, 35, 255))

    draw = ImageDraw.Draw(img)
    w, h = img.size

    print(f"[DAILY IMAGE] template_size={img.size}")

    white = (255, 255, 255)
    black = (0, 0, 0)

    # =========================
    # POSITIONS
    # =========================

    # Wins box (left)
    wins_x = int(w * 0.23)
    wins_y = int(h * 0.54)

    # Lost box (center)
    lost_x = int(w * 0.50)
    lost_y = int(h * 0.54)

    # Winrate box (right)
    winrate_x = int(w * 0.77)
    winrate_y = int(h * 0.54)

    # Date (above lost)
    date_x = lost_x
    date_y = int(h * 0.36)

    # Total picks
    total_x = int(w * 0.62)
    total_y = int(h * 0.695)

    total_picks = str(int(wins) + int(lost))

    # =========================
    # DATE
    # =========================
    draw_text(
        base_img=img,
        draw=draw,
        x=date_x,
        y=date_y,
        text=str(date_text),
        size=int(h * 0.045),
        fill=white,
        stroke_fill=black,
        bold=True,
        anchor="mm",
    )

    # =========================
    # WINS
    # =========================
    draw_text(
        base_img=img,
        draw=draw,
        x=wins_x,
        y=wins_y,
        text=str(wins),
        size=int(h * 0.085),
        fill=white,
        stroke_fill=black,
        bold=True,
        anchor="mm",
    )

    # =========================
    # LOST
    # =========================
    draw_text(
        base_img=img,
        draw=draw,
        x=lost_x,
        y=lost_y,
        text=str(lost),
        size=int(h * 0.085),
        fill=white,
        stroke_fill=black,
        bold=True,
        anchor="mm",
    )

    # =========================
    # WINRATE
    # =========================
    draw_text(
        base_img=img,
        draw=draw,
        x=winrate_x,
        y=winrate_y,
        text=str(winrate),
        size=int(h * 0.075),
        fill=white,
        stroke_fill=black,
        bold=True,
        anchor="mm",
    )

    # =========================
    # TOTAL PICKS
    # =========================
    draw_text(
        base_img=img,
        draw=draw,
        x=total_x,
        y=total_y,
        text=total_picks,
        size=int(h * 0.055),
        fill=white,
        stroke_fill=black,
        bold=True,
        anchor="mm",
    )

    filename = f"/tmp/daily_{int(time.time())}.jpg"
    img.convert("RGB").save(filename, "JPEG", quality=95)

    print(f"[DAILY IMAGE] Saved to {filename}")
    return filename
