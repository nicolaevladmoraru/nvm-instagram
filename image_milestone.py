import os
import time
from PIL import Image, ImageDraw

from font_utils import draw_text

TEMPLATE_PATH = "templates/template_milestone.png"


def build_milestone_image(title, date_text, wins, lost, winrate):
    if os.path.exists(TEMPLATE_PATH):
        img = Image.open(TEMPLATE_PATH).convert("RGBA")
    else:
        img = Image.new("RGBA", (1024, 1024), (10, 15, 35, 255))

    draw = ImageDraw.Draw(img)
    w, h = img.size

    print(f"[MILESTONE IMAGE] template_size={img.size}")

    white = (255, 255, 255)
    black = (0, 0, 0)

    # =========================
    # VALUES
    # =========================
    total_matches = str(date_text)
    wins_value = str(wins)
    lost_value = str(lost)
    winrate_value = str(winrate)

    # =========================
    # POSITIONS
    # =========================

    # Total Matches
    total_matches_x = int(w * 0.25)
    total_matches_y = int(h * 0.64)

    # Wins
    wins_x = int(w * 0.42)
    wins_y = int(h * 0.55)

    # Losts
    lost_x = int(w * 0.65)
    lost_y = int(h * 0.55)

    # Win Rate
    winrate_x = int(w * 0.86)
    winrate_y = int(h * 0.55)

    # =========================
    # TOTAL MATCHES
    # =========================
    draw_text(
        base_img=img,
        draw=draw,
        x=total_matches_x,
        y=total_matches_y,
        text=total_matches,
        size=int(h * 0.060),
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
        text=wins_value,
        size=int(h * 0.060),
        fill=white,
        stroke_fill=black,
        bold=True,
        anchor="mm",
    )

    # =========================
    # LOSTS
    # =========================
    draw_text(
        base_img=img,
        draw=draw,
        x=lost_x,
        y=lost_y,
        text=lost_value,
        size=int(h * 0.060),
        fill=white,
        stroke_fill=black,
        bold=True,
        anchor="mm",
    )

    # =========================
    # WIN RATE
    # =========================
    draw_text(
        base_img=img,
        draw=draw,
        x=winrate_x,
        y=winrate_y,
        text=winrate_value,
        size=int(h * 0.055),
        fill=white,
        stroke_fill=black,
        bold=True,
        anchor="mm",
    )

    filename = f"/tmp/milestone_{int(time.time())}.jpg"
    img.convert("RGB").save(filename, "JPEG", quality=95)

    print(f"[MILESTONE IMAGE] Saved to {filename}")
    return filename
