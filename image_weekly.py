import os
import time
from PIL import Image, ImageDraw

from font_utils import draw_text

TEMPLATE_PATH = "templates/template_weekly_report.png"


def build_weekly_image(title, date_text, wins, lost, winrate):
    if os.path.exists(TEMPLATE_PATH):
        img = Image.open(TEMPLATE_PATH).convert("RGBA")
    else:
        img = Image.new("RGBA", (1024, 1024), (10, 15, 35, 255))

    draw = ImageDraw.Draw(img)
    w, h = img.size

    print(f"[WEEKLY IMAGE] template_size={img.size}")

    white = (255, 255, 255)
    black = (0, 0, 0)

    # =========================
    # CLEAN DATE (REMOVE "-")
    # =========================
    date_text = str(date_text).replace("-", " ").replace("  ", " ").strip()

    # =========================
    # POSITIONS (LIKE DAILY)
    # =========================

    # Wins
    wins_x = int(w * 0.21)
    wins_y = int(h * 0.54)

    # Lost
    lost_x = int(w * 0.49)
    lost_y = int(h * 0.54)

    # Winrate
    winrate_x = int(w * 0.79)
    winrate_y = int(h * 0.54)

    # Date (above LOST)
    date_x = lost_x
    date_y = int(h * 0.34)

    # Total picks
    total_x = int(w * 0.65)
    total_y = int(h * 0.70)

    total_picks = str(int(wins) + int(lost))

    # =========================
    # DATE (WITH BIGGER SPACING)
    # =========================
    spaced_date = "   ".join(date_text.split())

    draw_text(
        base_img=img,
        draw=draw,
        x=date_x,
        y=date_y,
        text=spaced_date,
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
        size=int(h * 0.050),
        fill=white,
        stroke_fill=black,
        bold=True,
        anchor="mm",
    )

    filename = f"/tmp/weekly_{int(time.time())}.jpg"
    img.convert("RGB").save(filename, "JPEG", quality=95)

    print(f"[WEEKLY IMAGE] Saved to {filename}")
    return filename
