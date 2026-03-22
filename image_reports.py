import os
import time
from PIL import Image, ImageDraw

from config import TEMPLATE_PATH
from font_utils import draw_text


def draw_glow_circle(draw, center_x, center_y, radius, fill_color, outline_color):
    # outer soft rings
    for extra, alpha_like in [(28, 40), (18, 70), (10, 110)]:
        x0 = center_x - radius - extra
        y0 = center_y - radius - extra
        x1 = center_x + radius + extra
        y1 = center_y + radius + extra
        draw.ellipse(
            (x0, y0, x1, y1),
            outline=(outline_color[0], outline_color[1], outline_color[2]),
            width=2
        )

    # main circle
    x0 = center_x - radius
    y0 = center_y - radius
    x1 = center_x + radius
    y1 = center_y + radius
    draw.ellipse((x0, y0, x1, y1), fill=fill_color, outline=outline_color, width=5)


def build_report_image(report_type, title, date_text, wins, lost, winrate):
    if os.path.exists(TEMPLATE_PATH):
        img = Image.open(TEMPLATE_PATH).convert("RGBA")
    else:
        img = Image.new("RGBA", (1024, 1024), (10, 15, 35, 255))

    draw = ImageDraw.Draw(img)
    w, h = img.size
    print(f"[REPORT IMAGE] template_size={img.size}")

    gold = (242, 196, 78)
    white = (255, 255, 255)
    black = (0, 0, 0)
    dark_gold = (185, 132, 24)

    center_x = int(w * 0.50)

    # ================================
    # HEADER
    # ================================
    if report_type == "daily":
        header_text = "NVM DAILY REPORT"
    elif report_type == "weekly":
        header_text = "NVM WEEKLY REPORT"
    elif report_type == "monthly":
        header_text = "NVM MONTHLY REPORT"
    elif report_type == "milestone":
        header_text = "NVM MILESTONE"
    else:
        header_text = str(title or "NVM REPORT")

    # ================================
    # SIZES
    # ================================
    title_size = int(h * 0.050)
    date_size = int(h * 0.034)

    stat_label_size = int(h * 0.044)
    stat_value_size = int(h * 0.066)

    badge_label_size = int(h * 0.038)
    badge_value_size = int(h * 0.095)

    title_fallback_h = int(h * 0.054)
    date_fallback_h = int(h * 0.038)

    stat_label_fallback_h = int(h * 0.046)
    stat_value_fallback_h = int(h * 0.070)

    badge_label_fallback_h = int(h * 0.040)
    badge_value_fallback_h = int(h * 0.100)

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

    # DATE / PERIOD / x100 alerts
    draw_text(
        base_img=img,
        draw=draw,
        x=center_x,
        y=int(h * 0.145),
        text=str(date_text),
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

    # WINS
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

    # LOST
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
    # PREMIUM WIN RATE BADGE
    # ================================
    badge_center_x = int(w * 0.33)
    badge_center_y = int(h * 0.73)
    badge_radius = int(h * 0.105)

    draw_glow_circle(
        draw=draw,
        center_x=badge_center_x,
        center_y=badge_center_y,
        radius=badge_radius,
        fill_color=dark_gold,
        outline_color=gold,
    )

    # small label above percent
    draw_text(
        base_img=img,
        draw=draw,
        x=badge_center_x,
        y=int(badge_center_y - badge_radius * 0.38),
        text="WIN RATE",
        size=badge_label_size,
        fill=white,
        stroke_fill=black,
        bold=True,
        anchor="mm",
        fallback_height=badge_label_fallback_h,
    )

    # big percent in center
    draw_text(
        base_img=img,
        draw=draw,
        x=badge_center_x,
        y=int(badge_center_y + badge_radius * 0.10),
        text=str(winrate),
        size=badge_value_size,
        fill=white,
        stroke_fill=black,
        bold=True,
        anchor="mm",
        fallback_height=badge_value_fallback_h,
    )

    filename = f"/tmp/report_{int(time.time())}.jpg"
    img.convert("RGB").save(filename, "JPEG", quality=95)
    print(f"[REPORT IMAGE] Saved to {filename} | final_size={img.size}")
    return filename
