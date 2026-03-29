import io
import os
import time
from typing import Optional, Tuple

import requests
from PIL import Image, ImageDraw, ImageOps

from font_utils import draw_text, get_truetype_font, wrap_text_by_pixels

TEMPLATE_PATH = "templates/template_live_alert_base.png"


def _download_logo(url: Optional[str], size: Tuple[int, int]) -> Optional[Image.Image]:
    if not url:
        return None

    try:
        response = requests.get(str(url).strip(), timeout=10)
        response.raise_for_status()

        logo = Image.open(io.BytesIO(response.content)).convert("RGBA")
        logo = ImageOps.contain(logo, size)

        canvas = Image.new("RGBA", size, (0, 0, 0, 0))
        paste_x = (size[0] - logo.width) // 2
        paste_y = (size[1] - logo.height) // 2
        canvas.paste(logo, (paste_x, paste_y), logo)
        return canvas
    except Exception:
        return None


def build_alert_image(
    league,
    home,
    away,
    minute,
    score,
    pick,
    home_logo_url=None,
    away_logo_url=None,
    home_color=None,
    away_color=None,
):
    if os.path.exists(TEMPLATE_PATH):
        img = Image.open(TEMPLATE_PATH).convert("RGBA")
    else:
        img = Image.new("RGBA", (1024, 1024), (0, 0, 0, 255))

    w, h = img.size
    print(f"[ALERT IMAGE] template_size={img.size}")

    draw = ImageDraw.Draw(img)

    white = (255, 255, 255)
    gold = (242, 196, 78)
    black = (0, 0, 0)

    center_x = int(w * 0.50)

    # =========================
    # TEXT SIZES
    # =========================
    league_size = int(h * 0.040)
    vs_size = int(h * 0.055)
    minute_size = int(h * 0.038)
    score_size = int(h * 0.12)
    team_size = int(h * 0.050)
    pick_size = int(h * 0.058)

    league_fallback_h = int(h * 0.042)
    vs_fallback_h = int(h * 0.058)
    minute_fallback_h = int(h * 0.040)
    score_fallback_h = int(h * 0.100)
    team_fallback_h = int(h * 0.052)
    pick_fallback_h = int(h * 0.060)

    league_text = str(league or "").strip().upper()
    home_text = str(home or "").strip().upper()
    away_text = str(away or "").strip().upper()
    minute_text = f"MIN {str(minute).strip()}'"
    score_text = str(score or "").strip()
    pick_text = str(pick or "").strip().upper()

    # =========================
    # LEAGUE
    # =========================
    league_wrap_font = get_truetype_font(max(20, int(h * 0.028)), bold=True)
    if league_wrap_font:
        league_lines = wrap_text_by_pixels(draw, league_text, league_wrap_font, int(w * 0.78))
    else:
        league_lines = [league_text]

    league_y = int(h * 0.05)
    for i, line in enumerate(league_lines[:2]):
        draw_text(
            base_img=img,
            draw=draw,
            x=center_x,
            y=league_y + i * int(h * 0.042),
            text=line,
            size=league_size,
            fill=white,
            stroke_fill=black,
            bold=True,
            anchor="mm",
            fallback_height=league_fallback_h,
        )

    # =========================
    # TEAM LOGOS
    # =========================
    logo_size = (int(w * 0.22), int(w * 0.22))
    home_logo = _download_logo(home_logo_url, logo_size)
    away_logo = _download_logo(away_logo_url, logo_size)

    home_logo_x = int(w * 0.14)
    away_logo_x = int(w * 0.64)
    logos_y = int(h * 0.10)

    if home_logo is not None:
        img.paste(home_logo, (home_logo_x, logos_y), home_logo)

    if away_logo is not None:
        img.paste(away_logo, (away_logo_x, logos_y), away_logo)

    # =========================
    # VS
    # =========================
    draw_text(
        base_img=img,
        draw=draw,
        x=center_x,
        y=int(h * 0.39),
        text="VS",
        size=vs_size,
        fill=gold,
        stroke_fill=black,
        bold=True,
        anchor="mm",
        fallback_height=vs_fallback_h,
    )

    # =========================
    # MINUTE
    # =========================
    draw_text(
        base_img=img,
        draw=draw,
        x=center_x,
        y=int(h * 0.46),
        text=minute_text,
        size=minute_size,
        fill=gold,
        stroke_fill=black,
        bold=True,
        anchor="mm",
        fallback_height=minute_fallback_h,
    )

    # =========================
    # SCORE
    # =========================
    draw_text(
        base_img=img,
        draw=draw,
        x=center_x,
        y=int(h * 0.15),
        text=score_text,
        size=score_size,
        fill=gold,
        stroke_fill=black,
        bold=True,
        anchor="mm",
        fallback_height=score_fallback_h,
    )

    # =========================
    # TEAM NAMES
    # =========================
    draw_text(
        base_img=img,
        draw=draw,
        x=int(w * 0.26),
        y=int(h * 0.63),
        text=home_text,
        size=team_size,
        fill=white,
        stroke_fill=black,
        bold=True,
        anchor="mm",
        fallback_height=team_fallback_h,
    )

    draw_text(
        base_img=img,
        draw=draw,
        x=int(w * 0.74),
        y=int(h * 0.63),
        text=away_text,
        size=team_size,
        fill=white,
        stroke_fill=black,
        bold=True,
        anchor="mm",
        fallback_height=team_fallback_h,
    )

    # =========================
    # PICK CONTENT
    # =========================
    pick_wrap_font = get_truetype_font(max(22, int(h * 0.032)), bold=True)
    if pick_wrap_font:
        pick_lines = wrap_text_by_pixels(draw, pick_text, pick_wrap_font, int(w * 0.58))
    else:
        pick_lines = [pick_text]

    pick_y = int(h * 0.74)
    for i, line in enumerate(pick_lines[:2]):
        draw_text(
            base_img=img,
            draw=draw,
            x=center_x,
            y=pick_y + i * int(h * 0.045),
            text=line,
            size=pick_size,
            fill=gold,
            stroke_fill=black,
            bold=True,
            anchor="mm",
            fallback_height=pick_fallback_h,
        )

    filename = f"/tmp/alert_{int(time.time())}.jpg"
    img.convert("RGB").save(filename, "JPEG", quality=95)

    print(f"[ALERT IMAGE] Saved to {filename}")
    return filename
