import os
import time
from PIL import Image, ImageDraw

from config import TEMPLATE_PATH
from font_utils import draw_text


def build_weekly_image(title, date_text, wins, lost, winrate):
    if os.path.exists(TEMPLATE_PATH):
        img = Image.open(TEMPLATE_PATH).convert("RGBA")
    else:
        img = Image.new("RGBA", (1024, 1024), (10, 15, 35, 255))

    draw = ImageDraw.Draw(img)
    w, h = img.size
    print(f"[WEEKLY IMAGE] template_size={img.size}")

    gold = (242, 196, 78)
    white = (255, 255, 255)
    black = (0, 0, 0)

    center_x = int(w * 0.50)

    header_text = str(title or "NVM WEEKLY REPORT").strip()
    if not header_text:
        header_text = "NVM WEEKLY REPORT"

    # ================================
    # SIZES
    # ================================
    title_size = int(h * 0.050)
    date_size = int(h * 0.034)

    stat_label_size = int(h * 0.044)
    stat_value_size = int(h * 0.066)

    winrate_label_size = int(h * 0.045)
    winrate_value_size = int(h * 0.105)

    title_fallback_h = int(h * 0.054)
    date_fallback_h = int(h * 0.038)

    stat_label_fallback_h = int(h * 0.046)
    stat_value_fallback_h = int(h * 0.070)

    winrate_label_fallback_h = int(h * 0.048)
    winrate_value_fallback_h = int(h * 0.110)

    # ================================
    # TITLE
    # ================================
    draw_text(
        base_img=img,
        draw=draw,
        x=center_x,
        y=int(h * 0.065),
        text=header_text,
        size=title_size,
        fill=gold,
        stroke_fill=black,
        bold=True,
        anchor="mm",
        fallback_height=title_fallback_h,
    )

    # ================================
    # PERIOD / DATE RANGE
    # ================================
    draw_text(
        base_img=img,
        draw=draw,
        x=center_x,
        y=int(h * 0.145),
        text=str(date_text or ""),
        size=date_size,
        fill=white,
        stroke_fill=black,
        bold=True,
        anchor="mm",
        fallback_height=date_fallback_h,
    )

    # ================================
    # LEFT STATS
    # ================================
    x_label = int(w * 0.11)
    x_value = int(w * 0.42)

    y_start = int(h * 0.35)
    row_gap = int(h * 0.12)

    draw_text(
        base_img=img,
        draw=draw,
        x=x_label,
        y=y_start,
        text="WINS:",
        size=stat_label_size,
        fill=gold,
        stroke_fill=black,
        bold=True,
        anchor="lt",
        fallback_height=stat_label_fallback_h,
    )
    draw_text(
        base_img=img,
        draw=draw,
        x=x_value,
        y=y_start,
        text=str(wins),
        size=stat_value_size,
        fill=white,
        stroke_fill=black,
        bold=True,
        anchor="lt",
        fallback_height=stat_value_fallback_h,
    )

    draw_text(
        base_img=img,
        draw=draw,
        x=x_label,
        y=y_start + row_gap,
        text="LOST:",
        size=stat_label_size,
        fill=gold,
        stroke_fill=black,
        bold=True,
        anchor="lt",
        fallback_height=stat_label_fallback_h,
    )
    draw_text(
        base_img=img,
        draw=draw,
        x=x_value,
        y=y_start + row_gap,
        text=str(lost),
        size=stat_value_size,
        fill=white,
        stroke_fill=black,
        bold=True,
        anchor="lt",
        fallback_height=stat_value_fallback_h,
    )

    # ================================
    # WIN RATE
    # ================================
    winrate_x = int(w * 0.33)
    winrate_label_y = int(h * 0.60)
    winrate_value_y = int(h * 0.70)

    draw_text(
        base_img=img,
        draw=draw,
        x=winrate_x,
        y=winrate_label_y,
        text="WIN RATE",
        size=winrate_label_size,
        fill=gold,
        stroke_fill=black,
        bold=True,
        anchor="mm",
        fallback_height=winrate_label_fallback_h,
    )

    draw_text(
        base_img=img,
        draw=draw,
        x=winrate_x,
        y=winrate_value_y,
        text=str(winrate),
        size=winrate_value_size,
        fill=white,
        stroke_fill=black,
        bold=True,
        anchor="mm",
        fallback_height=winrate_value_fallback_h,
    )

    filename = f"/tmp/weekly_report_{int(time.time())}.jpg"
    img.convert("RGB").save(filename, "JPEG", quality=95)
    print(f"[WEEKLY IMAGE] Saved to {filename} | final_size={img.size}")
    return filename
