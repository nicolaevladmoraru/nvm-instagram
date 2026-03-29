import io
import os
import time
from typing import Optional, Tuple

import requests
from PIL import Image, ImageDraw, ImageFilter, ImageOps

from font_utils import draw_text, get_truetype_font, wrap_text_by_pixels

TEMPLATE_PATH = "templates/template_live_alert_base.png"

DEFAULT_LEFT_COLOR = (120, 20, 20)
DEFAULT_RIGHT_COLOR = (20, 50, 120)

TEAM_COLORS = {
    "Arsenal": (180, 20, 20),
    "Chelsea": (20, 60, 140),
    "Liverpool": (170, 20, 20),
    "Manchester City": (90, 170, 220),
    "Man City": (90, 170, 220),
    "Manchester United": (170, 20, 20),
    "Man United": (170, 20, 20),
    "Tottenham": (220, 220, 220),
    "Spurs": (220, 220, 220),
    "Barcelona": (140, 20, 40),
    "Real Madrid": (220, 220, 220),
    "Atletico Madrid": (170, 40, 40),
    "Juventus": (200, 200, 200),
    "Inter": (20, 50, 130),
    "Milan": (150, 20, 20),
    "AC Milan": (150, 20, 20),
    "Napoli": (40, 140, 220),
    "PSG": (30, 50, 120),
    "Paris Saint Germain": (30, 50, 120),
    "Bayern Munich": (170, 20, 20),
    "Bayern": (170, 20, 20),
    "Borussia Dortmund": (220, 190, 20),
    "Dortmund": (220, 190, 20),
    "Newcastle": (60, 60, 60),
    "Aston Villa": (120, 40, 80),
    "Leicester": (30, 70, 180),
    "Everton": (30, 70, 160),
    "West Ham": (110, 30, 60),
    "Roma": (130, 30, 20),
    "Lazio": (120, 180, 220),
    "Benfica": (170, 20, 20),
    "Porto": (20, 60, 140),
    "Sporting": (20, 120, 60),
}


def _normalize_team_name(team_name: str) -> str:
    return str(team_name or "").strip()


def _get_team_color(team_name: str, fallback: Tuple[int, int, int]) -> Tuple[int, int, int]:
    team_name = _normalize_team_name(team_name)
    if team_name in TEAM_COLORS:
        return TEAM_COLORS[team_name]
    return fallback


def _parse_color(value, fallback: Tuple[int, int, int]) -> Tuple[int, int, int]:
    if isinstance(value, (list, tuple)) and len(value) == 3:
        try:
            r = int(value[0])
            g = int(value[1])
            b = int(value[2])
            return (max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b)))
        except Exception:
            return fallback
    return fallback


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


def _make_black_transparent(img: Image.Image, threshold: int = 18) -> Image.Image:
    img = img.convert("RGBA")
    pixels = img.load()
    width, height = img.size

    for y in range(height):
        for x in range(width):
            r, g, b, a = pixels[x, y]
            if r <= threshold and g <= threshold and b <= threshold:
                pixels[x, y] = (r, g, b, 0)

    return img


def _build_dynamic_background(
    width: int,
    height: int,
    left_color: Tuple[int, int, int],
    right_color: Tuple[int, int, int],
) -> Image.Image:
    bg = Image.new("RGBA", (width, height), (0, 0, 0, 255))
    px = bg.load()

    for x in range(width):
        t = x / max(1, width - 1)

        r = int(left_color[0] * (1 - t) + right_color[0] * t)
        g = int(left_color[1] * (1 - t) + right_color[1] * t)
        b = int(left_color[2] * (1 - t) + right_color[2] * t)

        for y in range(height):
            px[x, y] = (r, g, b, 255)

    dark_overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    dark_draw = ImageDraw.Draw(dark_overlay)

    # Dark center to keep text readable
    dark_draw.rectangle(
        [0, 0, width, height],
        fill=(0, 0, 0, 90),
    )

    # Soft center glow
    glow = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    glow_draw.ellipse(
        [int(width * 0.22), int(height * 0.12), int(width * 0.78), int(height * 0.80)],
        fill=(255, 255, 255, 24),
    )
    glow = glow.filter(ImageFilter.GaussianBlur(70))

    # Vignette
    vignette = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    vig_draw = ImageDraw.Draw(vignette)
    vig_draw.rectangle([0, 0, width, height], fill=(0, 0, 0, 70))
    vignette = vignette.filter(ImageFilter.GaussianBlur(40))

    bg = Image.alpha_composite(bg, glow)
    bg = Image.alpha_composite(bg, dark_overlay)
    bg = Image.alpha_composite(bg, vignette)

    return bg


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
        template = Image.open(TEMPLATE_PATH).convert("RGBA")
    else:
        template = Image.new("RGBA", (1024, 1024), (0, 0, 0, 255))

    w, h = template.size
    print(f"[ALERT IMAGE] template_size={template.size}")

    left_color = _parse_color(
        home_color,
        _get_team_color(str(home), DEFAULT_LEFT_COLOR),
    )
    right_color = _parse_color(
        away_color,
        _get_team_color(str(away), DEFAULT_RIGHT_COLOR),
    )

    base = _build_dynamic_background(w, h, left_color, right_color)

    template_overlay = _make_black_transparent(template, threshold=18)
    img = Image.alpha_composite(base, template_overlay)

    draw = ImageDraw.Draw(img)

    white = (255, 255, 255)
    gold = (242, 196, 78)
    black = (0, 0, 0)

    center_x = int(w * 0.50)

    league_size = int(h * 0.042)
    vs_size = int(h * 0.058)
    minute_size = int(h * 0.040)
    score_size = int(h * 0.090)
    team_size = int(h * 0.052)
    pick_size = int(h * 0.060)

    league_fallback_h = int(h * 0.044)
    vs_fallback_h = int(h * 0.062)
    minute_fallback_h = int(h * 0.042)
    score_fallback_h = int(h * 0.095)
    team_fallback_h = int(h * 0.054)
    pick_fallback_h = int(h * 0.062)

    league_text = str(league or "").strip().upper()
    home_text = str(home or "").strip().upper()
    away_text = str(away or "").strip().upper()
    minute_text = f"MIN {str(minute).strip()}'"
    score_text = str(score or "").strip()
    pick_text = str(pick or "").strip().upper()

    # League
    league_wrap_font = get_truetype_font(max(20, int(h * 0.028)), bold=True)
    if league_wrap_font:
        league_lines = wrap_text_by_pixels(draw, league_text, league_wrap_font, int(w * 0.78))
    else:
        league_lines = [league_text]

    league_y = int(h * 0.12)
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

    # Logos
    logo_size = (int(w * 0.20), int(w * 0.20))
    home_logo = _download_logo(home_logo_url, logo_size)
    away_logo = _download_logo(away_logo_url, logo_size)

    home_logo_x = int(w * 0.16)
    away_logo_x = int(w * 0.64)
    logos_y = int(h * 0.24)

    if home_logo is not None:
        img.paste(home_logo, (home_logo_x, logos_y), home_logo)

    if away_logo is not None:
        img.paste(away_logo, (away_logo_x, logos_y), away_logo)

    # VS
    draw_text(
        base_img=img,
        draw=draw,
        x=center_x,
        y=int(h * 0.37),
        text="VS",
        size=vs_size,
        fill=gold,
        stroke_fill=black,
        bold=True,
        anchor="mm",
        fallback_height=vs_fallback_h,
    )

    # Minute
    draw_text(
        base_img=img,
        draw=draw,
        x=center_x,
        y=int(h * 0.44),
        text=minute_text,
        size=minute_size,
        fill=gold,
        stroke_fill=black,
        bold=True,
        anchor="mm",
        fallback_height=minute_fallback_h,
    )

    # Score
    draw_text(
        base_img=img,
        draw=draw,
        x=center_x,
        y=int(h * 0.52),
        text=score_text,
        size=score_size,
        fill=gold,
        stroke_fill=black,
        bold=True,
        anchor="mm",
        fallback_height=score_fallback_h,
    )

    # Team names
    draw_text(
        base_img=img,
        draw=draw,
        x=int(w * 0.26),
        y=int(h * 0.60),
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
        y=int(h * 0.60),
        text=away_text,
        size=team_size,
        fill=white,
        stroke_fill=black,
        bold=True,
        anchor="mm",
        fallback_height=team_fallback_h,
    )

    # Pick content
    pick_wrap_font = get_truetype_font(max(22, int(h * 0.032)), bold=True)
    if pick_wrap_font:
        pick_lines = wrap_text_by_pixels(draw, pick_text, pick_wrap_font, int(w * 0.58))
    else:
        pick_lines = [pick_text]

    pick_y = int(h * 0.73)
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
