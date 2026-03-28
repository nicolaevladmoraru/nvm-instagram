import os
import time
from PIL import Image, ImageDraw, ImageFont

from font_utils import draw_text, get_truetype_font, wrap_text_by_pixels

TEMPLATE_PATH = "templates/template_live_alerts.png"


def build_alert_image(league, home, away, minute, score, pick):
    if os.path.exists(TEMPLATE_PATH):
        img = Image.open(TEMPLATE_PATH).convert("RGBA")
    else:
        img = Image.new("RGBA", (1024, 1024), (10, 15, 35, 255))

    draw = ImageDraw.Draw(img)
    w, h = img.size
    print(f"[ALERT IMAGE] template_size={img.size}")

    gold = (242, 196, 78)
    white = (255, 255, 255)
    black = (0, 0, 0)

    center_x = int(w * 0.50)

    title_size = int(h * 0.044)
    league_size = int(h * 0.042)
    match_size = int(h * 0.062)
    label_size = int(h * 0.046)
    value_size = int(h * 0.054)
    pick_size = int(h * 0.044)

    title_fallback_h = int(h * 0.046)
    league_fallback_h = int(h * 0.045)
    match_fallback_h = int(h * 0.068)
    label_fallback_h = int(h * 0.048)
    value_fallback_h = int(h * 0.058)
    pick_fallback_h = int(h * 0.046)

    draw_text(
        base_img=img,
        draw=draw,
        x=center_x,
        y=int(h * 0.055),
        text="NVM LIVE ALERT",
        size=title_size,
        fill=gold,
        stroke_fill=black,
        bold=True,
        anchor="mm",
        fallback_height=title_fallback_h,
    )

    wrap_font = get_truetype_font(max(22, int(h * 0.032)), bold=True) or ImageFont.load_default()

    league_lines = wrap_text_by_pixels(draw, str(league), wrap_font, int(w * 0.68))
    league_y = int(h * 0.145)
    for i, line in enumerate(league_lines[:2]):
        draw_text(
            base_img=img,
            draw=draw,
            x=center_x,
            y=league_y + i * int(h * 0.044),
            text=line,
            size=league_size,
            fill=white,
            stroke_fill=black,
            bold=True,
            anchor="mm",
            fallback_height=league_fallback_h,
        )

    match_text = f"{home} vs {away}"
    match_lines = wrap_text_by_pixels(draw, match_text, wrap_font, int(w * 0.74))
    match_y = int(h * 0.245)
    for i, line in enumerate(match_lines[:2]):
        draw_text(
            base_img=img,
            draw=draw,
            x=center_x,
            y=match_y + i * int(h * 0.055),
            text=line,
            size=match_size,
            fill=white,
            stroke_fill=black,
            bold=True,
            anchor="mm",
            fallback_height=match_fallback_h,
        )

    x_label = int(w * 0.08)
    x_value = int(w * 0.30)
    y_start = int(h * 0.40)
    row_gap = int(h * 0.095)

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

    draw_text(
        base_img=img,
        draw=draw,
        x=x_label,
        y=y_start + row_gap * 2,
        text="PICK:",
        size=label_size,
        fill=gold,
        stroke_fill=black,
        bold=True,
        anchor="lt",
        fallback_height=label_fallback_h,
    )

    pick_wrap_font = get_truetype_font(max(20, int(h * 0.027)), bold=True) or ImageFont.load_default()
    pick_lines = wrap_text_by_pixels(draw, str(pick), pick_wrap_font, int(w * 0.18))
    for i, line in enumerate(pick_lines[:3]):
        draw_text(
            base_img=img,
            draw=draw,
            x=x_value,
            y=y_start + row_gap * 2 + i * int(h * 0.040),
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
    print(f"[ALERT IMAGE] Saved to {filename} | final_size={img.size}")
    return filename
