import io
import math
import os
import random
import time
from typing import Optional, Tuple, List

import requests
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

TEMPLATE_PATH = "templates/template_live_alert_base.png"
FONT_DIR = "fonts"

IMAGE_SIZE = (1024, 1024)

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GOLD = (242, 196, 78)
SOFT_GOLD = (255, 214, 102)
RED = (230, 57, 70)
GREEN = (39, 174, 96)
DARK_GREEN = (8, 54, 29)
LIGHT_GREEN = (76, 175, 80)
SILVER = (210, 215, 220)


FONT_FILES = {
    "impact": "Impact.ttf",
    "bebas": "BebasNeue-Regular.ttf",
    "montserrat_bold": "MontserratBold.ttf",
    "montserrat_regular": "MontserratRegular.ttf",
    "oswald": "OSWALD.otf",
    "roboto_bold": "Roboto-Bold.ttf",
    "heart": "HeartBubble.otf",
}


STYLE_PRESETS = [
    {
        "name": "dark_premium",
        "bg_mode": "stadium_night",
        "overlay": "gold_glow",
        "badge_fill": (18, 18, 18, 220),
        "badge_text": GOLD,
        "score_fill": GOLD,
        "score_stroke": BLACK,
        "pick_fill": GOLD,
        "pick_box": (18, 18, 18, 210),
        "team_fill": WHITE,
        "league_fill": WHITE,
        "minute_fill": SOFT_GOLD,
        "use_pitch": True,
        "use_crowd": True,
        "accent_line": GOLD,
        "headline_font": "impact",
        "score_font": "impact",
        "team_font": "bebas",
        "league_font": "montserrat_bold",
        "pick_font": "oswald",
    },
    {
        "name": "goal_alert_red",
        "bg_mode": "breaking_red",
        "overlay": "red_glow",
        "badge_fill": (145, 16, 26, 225),
        "badge_text": WHITE,
        "score_fill": WHITE,
        "score_stroke": BLACK,
        "pick_fill": WHITE,
        "pick_box": (145, 16, 26, 220),
        "team_fill": WHITE,
        "league_fill": WHITE,
        "minute_fill": WHITE,
        "use_pitch": False,
        "use_crowd": True,
        "accent_line": RED,
        "headline_font": "impact",
        "score_font": "impact",
        "team_font": "oswald",
        "league_font": "montserrat_bold",
        "pick_font": "impact",
    },
    {
        "name": "pitch_focus",
        "bg_mode": "pitch",
        "overlay": "green_glow",
        "badge_fill": (0, 0, 0, 185),
        "badge_text": GOLD,
        "score_fill": WHITE,
        "score_stroke": BLACK,
        "pick_fill": GOLD,
        "pick_box": (0, 0, 0, 195),
        "team_fill": WHITE,
        "league_fill": WHITE,
        "minute_fill": SOFT_GOLD,
        "use_pitch": True,
        "use_crowd": False,
        "accent_line": LIGHT_GREEN,
        "headline_font": "bebas",
        "score_font": "impact",
        "team_font": "bebas",
        "league_font": "montserrat_bold",
        "pick_font": "oswald",
    },
    {
        "name": "clean_modern",
        "bg_mode": "clean_blue_night",
        "overlay": "blue_glow",
        "badge_fill": (255, 255, 255, 220),
        "badge_text": (15, 15, 15),
        "score_fill": WHITE,
        "score_stroke": BLACK,
        "pick_fill": WHITE,
        "pick_box": (17, 35, 56, 215),
        "team_fill": WHITE,
        "league_fill": WHITE,
        "minute_fill": SILVER,
        "use_pitch": False,
        "use_crowd": True,
        "accent_line": (80, 175, 255),
        "headline_font": "roboto_bold",
        "score_font": "impact",
        "team_font": "roboto_bold",
        "league_font": "montserrat_bold",
        "pick_font": "oswald",
    },
    {
        "name": "ultra_fomo",
        "bg_mode": "crowd_fire",
        "overlay": "orange_glow",
        "badge_fill": (255, 102, 0, 230),
        "badge_text": WHITE,
        "score_fill": WHITE,
        "score_stroke": BLACK,
        "pick_fill": WHITE,
        "pick_box": (255, 102, 0, 215),
        "team_fill": WHITE,
        "league_fill": WHITE,
        "minute_fill": WHITE,
        "use_pitch": False,
        "use_crowd": True,
        "accent_line": (255, 135, 44),
        "headline_font": "impact",
        "score_font": "impact",
        "team_font": "bebas",
        "league_font": "montserrat_bold",
        "pick_font": "impact",
    },
    {
        "name": "premium_green_gold",
        "bg_mode": "emerald_gold",
        "overlay": "gold_glow",
        "badge_fill": (20, 45, 20, 220),
        "badge_text": GOLD,
        "score_fill": GOLD,
        "score_stroke": BLACK,
        "pick_fill": GOLD,
        "pick_box": (16, 42, 20, 205),
        "team_fill": WHITE,
        "league_fill": WHITE,
        "minute_fill": SOFT_GOLD,
        "use_pitch": True,
        "use_crowd": True,
        "accent_line": GOLD,
        "headline_font": "bebas",
        "score_font": "impact",
        "team_font": "oswald",
        "league_font": "montserrat_bold",
        "pick_font": "oswald",
    },
    {
        "name": "minimal_black",
        "bg_mode": "black_spotlight",
        "overlay": "white_glow",
        "badge_fill": (255, 255, 255, 225),
        "badge_text": BLACK,
        "score_fill": WHITE,
        "score_stroke": BLACK,
        "pick_fill": WHITE,
        "pick_box": (18, 18, 18, 225),
        "team_fill": WHITE,
        "league_fill": SILVER,
        "minute_fill": SOFT_GOLD,
        "use_pitch": False,
        "use_crowd": False,
        "accent_line": WHITE,
        "headline_font": "roboto_bold",
        "score_font": "impact",
        "team_font": "bebas",
        "league_font": "montserrat_regular",
        "pick_font": "oswald",
    },
    {
        "name": "stadium_flash",
        "bg_mode": "stadium_flash",
        "overlay": "cyan_glow",
        "badge_fill": (0, 0, 0, 200),
        "badge_text": WHITE,
        "score_fill": WHITE,
        "score_stroke": BLACK,
        "pick_fill": WHITE,
        "pick_box": (0, 110, 170, 210),
        "team_fill": WHITE,
        "league_fill": WHITE,
        "minute_fill": SILVER,
        "use_pitch": True,
        "use_crowd": True,
        "accent_line": (0, 195, 255),
        "headline_font": "impact",
        "score_font": "impact",
        "team_font": "oswald",
        "league_font": "montserrat_bold",
        "pick_font": "roboto_bold",
    },
    {
        "name": "supporters_night",
        "bg_mode": "supporters_night",
        "overlay": "purple_glow",
        "badge_fill": (28, 22, 50, 220),
        "badge_text": WHITE,
        "score_fill": WHITE,
        "score_stroke": BLACK,
        "pick_fill": GOLD,
        "pick_box": (28, 22, 50, 215),
        "team_fill": WHITE,
        "league_fill": WHITE,
        "minute_fill": SOFT_GOLD,
        "use_pitch": False,
        "use_crowd": True,
        "accent_line": (161, 118, 255),
        "headline_font": "bebas",
        "score_font": "impact",
        "team_font": "bebas",
        "league_font": "montserrat_bold",
        "pick_font": "heart",
    },
    {
        "name": "grass_ball_spotlight",
        "bg_mode": "grass_ball",
        "overlay": "green_glow",
        "badge_fill": (0, 0, 0, 205),
        "badge_text": GOLD,
        "score_fill": WHITE,
        "score_stroke": BLACK,
        "pick_fill": WHITE,
        "pick_box": (0, 0, 0, 205),
        "team_fill": WHITE,
        "league_fill": WHITE,
        "minute_fill": SOFT_GOLD,
        "use_pitch": True,
        "use_crowd": False,
        "accent_line": LIGHT_GREEN,
        "headline_font": "impact",
        "score_font": "impact",
        "team_font": "oswald",
        "league_font": "montserrat_bold",
        "pick_font": "oswald",
    },
]


def _font_path(key: str) -> Optional[str]:
    filename = FONT_FILES.get(key)
    if not filename:
        return None

    full_path = os.path.join(FONT_DIR, filename)
    if os.path.exists(full_path):
        return full_path

    return None


def _load_font(font_key: str, size: int) -> ImageFont.FreeTypeFont:
    path = _font_path(font_key)
    if path:
        try:
            return ImageFont.truetype(path, max(12, int(size)))
        except Exception:
            pass

    try:
        return ImageFont.truetype("arial.ttf", max(12, int(size)))
    except Exception:
        return ImageFont.load_default()


def _safe_text(value) -> str:
    return str(value or "").strip()


def _text_bbox(draw: ImageDraw.ImageDraw, text: str, font, stroke_width: int = 0):
    return draw.textbbox((0, 0), _safe_text(text), font=font, stroke_width=stroke_width)


def _text_size(draw: ImageDraw.ImageDraw, text: str, font, stroke_width: int = 0) -> Tuple[int, int]:
    bbox = _text_bbox(draw, text, font, stroke_width=stroke_width)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def _fit_font(draw: ImageDraw.ImageDraw, text: str, font_key: str, start_size: int, min_size: int, max_width: int, stroke_width: int = 0):
    size = int(start_size)
    while size >= int(min_size):
        font = _load_font(font_key, size)
        width, _ = _text_size(draw, text, font, stroke_width=stroke_width)
        if width <= int(max_width):
            return font
        size -= 2
    return _load_font(font_key, min_size)


def _wrap_text(draw: ImageDraw.ImageDraw, text: str, font, max_width: int, stroke_width: int = 0, max_lines: int = 2) -> List[str]:
    text = _safe_text(text)
    if not text:
        return [""]

    words = text.split()
    if not words:
        return [""]

    lines: List[str] = []
    current = words[0]

    for word in words[1:]:
        candidate = f"{current} {word}"
        width, _ = _text_size(draw, candidate, font, stroke_width=stroke_width)
        if width <= int(max_width):
            current = candidate
        else:
            lines.append(current)
            current = word

    lines.append(current)

    if len(lines) <= max_lines:
        return lines

    compact = lines[: max_lines - 1]
    last_line_words = " ".join(lines[max_lines - 1 :].copy())
    compact.append(last_line_words)

    while True:
        width, _ = _text_size(draw, compact[-1], font, stroke_width=stroke_width)
        if width <= int(max_width) or len(compact[-1]) <= 3:
            break
        compact[-1] = compact[-1][:-4].rstrip() + "..."

    return compact


def _draw_center_text(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    text: str,
    font,
    fill,
    stroke_fill=(0, 0, 0),
    stroke_width: int = 2,
    anchor: str = "mm",
):
    draw.text(
        (int(x), int(y)),
        _safe_text(text),
        font=font,
        fill=fill,
        stroke_width=int(stroke_width),
        stroke_fill=stroke_fill,
        anchor=anchor,
    )


def _draw_multiline_center(
    draw: ImageDraw.ImageDraw,
    center_x: int,
    top_y: int,
    lines: List[str],
    font,
    fill,
    stroke_fill=(0, 0, 0),
    stroke_width: int = 2,
    spacing: int = 8,
):
    current_y = int(top_y)
    for line in lines:
        width, height = _text_size(draw, line, font, stroke_width=stroke_width)
        _draw_center_text(
            draw=draw,
            x=center_x,
            y=current_y,
            text=line,
            font=font,
            fill=fill,
            stroke_fill=stroke_fill,
            stroke_width=stroke_width,
            anchor="ma",
        )
        current_y += height + int(spacing)


def _download_logo(url: Optional[str], size: Tuple[int, int]) -> Optional[Image.Image]:
    if not url:
        return None

    try:
        response = requests.get(str(url).strip(), timeout=12)
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


def _draw_vertical_gradient(img: Image.Image, top_color: Tuple[int, int, int], bottom_color: Tuple[int, int, int]):
    width, height = img.size
    draw = ImageDraw.Draw(img)
    for y in range(height):
        t = y / max(1, height - 1)
        color = (
            int(top_color[0] * (1 - t) + bottom_color[0] * t),
            int(top_color[1] * (1 - t) + bottom_color[1] * t),
            int(top_color[2] * (1 - t) + bottom_color[2] * t),
            255,
        )
        draw.line((0, y, width, y), fill=color)


def _add_noise_dots(img: Image.Image, count: int, colors: List[Tuple[int, int, int, int]], radius_range=(1, 4)):
    draw = ImageDraw.Draw(img, "RGBA")
    width, height = img.size
    for _ in range(count):
        r = random.randint(radius_range[0], radius_range[1])
        x = random.randint(0, width)
        y = random.randint(0, height)
        fill = random.choice(colors)
        draw.ellipse((x - r, y - r, x + r, y + r), fill=fill)


def _draw_spotlight(img: Image.Image, center: Tuple[int, int], radius: int, color=(255, 255, 255, 120)):
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer, "RGBA")
    cx, cy = center

    for i in range(radius, 0, -16):
        alpha = int(color[3] * (i / radius) * 0.18)
        draw.ellipse((cx - i, cy - i, cx + i, cy + i), fill=(color[0], color[1], color[2], alpha))

    layer = layer.filter(ImageFilter.GaussianBlur(35))
    img.alpha_composite(layer)


def _draw_floodlights(img: Image.Image):
    width, height = img.size
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer, "RGBA")

    positions = [
        (int(width * 0.08), int(height * 0.10)),
        (int(width * 0.92), int(height * 0.10)),
        (int(width * 0.20), int(height * 0.06)),
        (int(width * 0.80), int(height * 0.06)),
    ]

    for x, y in positions:
        draw.rounded_rectangle((x - 35, y - 8, x + 35, y + 8), radius=4, fill=(255, 255, 235, 220))
        for i in range(7):
            lx = x - 30 + i * 10
            draw.rectangle((lx, y - 14, lx + 6, y + 14), fill=(255, 255, 240, 240))

    layer = layer.filter(ImageFilter.GaussianBlur(4))
    img.alpha_composite(layer)

    for x, y in positions:
        _draw_spotlight(img, (x, y + 20), radius=260, color=(255, 250, 210, 130))


def _draw_crowd_band(img: Image.Image, y_start: int, y_end: int, theme: str = "neutral"):
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer, "RGBA")
    width, _ = img.size

    if theme == "red":
        palette = [(155, 18, 31, 170), (210, 45, 60, 150), (255, 255, 255, 90), (20, 20, 20, 180)]
    elif theme == "purple":
        palette = [(75, 40, 140, 170), (140, 90, 220, 130), (255, 255, 255, 80), (20, 20, 20, 180)]
    else:
        palette = [(26, 26, 26, 180), (70, 70, 70, 160), (255, 255, 255, 70), (45, 120, 70, 100)]

    for _ in range(1700):
        x = random.randint(0, width)
        y = random.randint(y_start, y_end)
        w = random.randint(2, 7)
        h = random.randint(2, 7)
        fill = random.choice(palette)
        draw.ellipse((x, y, x + w, y + h), fill=fill)

    for _ in range(18):
        banner_w = random.randint(100, 260)
        x = random.randint(0, max(0, width - banner_w))
        y = random.randint(y_start + 10, max(y_start + 20, y_end - 10))
        draw.rounded_rectangle((x, y, x + banner_w, y + 10), radius=3, fill=random.choice(palette))

    layer = layer.filter(ImageFilter.GaussianBlur(1))
    img.alpha_composite(layer)


def _draw_pitch_lines(img: Image.Image, top_y: int, color=(255, 255, 255, 60)):
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer, "RGBA")
    width, height = img.size

    draw.rectangle((int(width * 0.08), top_y, int(width * 0.92), height - 30), outline=color, width=4)
    draw.line((int(width * 0.50), top_y, int(width * 0.50), height - 30), fill=color, width=3)
    draw.ellipse((int(width * 0.42), int(height * 0.73), int(width * 0.58), int(height * 0.89)), outline=color, width=3)

    box_top = int(height * 0.76)
    draw.rectangle((int(width * 0.25), box_top, int(width * 0.75), height - 30), outline=color, width=3)
    draw.rectangle((int(width * 0.38), int(height * 0.84), int(width * 0.62), height - 30), outline=color, width=3)

    layer = layer.filter(ImageFilter.GaussianBlur(0.4))
    img.alpha_composite(layer)


def _draw_grass_texture(img: Image.Image, top_color=(21, 90, 39), bottom_color=(10, 56, 25)):
    width, height = img.size
    _draw_vertical_gradient(img, top_color, bottom_color)

    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer, "RGBA")

    stripe_h = max(16, height // 18)
    for i in range(0, height, stripe_h):
        alpha = 22 if (i // stripe_h) % 2 == 0 else 0
        draw.rectangle((0, i, width, i + stripe_h), fill=(255, 255, 255, alpha))

    for _ in range(5500):
        x = random.randint(0, width)
        y = random.randint(0, height)
        length = random.randint(4, 10)
        g = random.randint(110, 170)
        draw.line((x, y, x + random.randint(-2, 2), y + length), fill=(20, g, 40, random.randint(16, 48)), width=1)

    layer = layer.filter(ImageFilter.GaussianBlur(0.4))
    img.alpha_composite(layer)


def _draw_ball(img: Image.Image, center: Tuple[int, int], radius: int):
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer, "RGBA")
    cx, cy = center

    shadow_box = (cx - radius + 18, cy + radius - 10, cx + radius + 36, cy + radius + 24)
    draw.ellipse(shadow_box, fill=(0, 0, 0, 90))

    draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), fill=(250, 250, 250, 255), outline=(20, 20, 20, 220), width=4)
    pentagon = [
        (cx, cy - int(radius * 0.34)),
        (cx + int(radius * 0.30), cy - int(radius * 0.12)),
        (cx + int(radius * 0.18), cy + int(radius * 0.22)),
        (cx - int(radius * 0.18), cy + int(radius * 0.22)),
        (cx - int(radius * 0.30), cy - int(radius * 0.12)),
    ]
    draw.polygon(pentagon, fill=(30, 30, 30, 255))

    for angle in [20, 90, 160, 235, 305]:
        rad = math.radians(angle)
        px = cx + int(math.cos(rad) * radius * 0.55)
        py = cy + int(math.sin(rad) * radius * 0.55)
        r = int(radius * 0.16)
        draw.ellipse((px - r, py - r, px + r, py + r), fill=(30, 30, 30, 255))

    layer = layer.filter(ImageFilter.GaussianBlur(0.4))
    img.alpha_composite(layer)
    _draw_spotlight(img, (cx - int(radius * 0.25), cy - int(radius * 0.30)), radius=int(radius * 1.3), color=(255, 255, 255, 50))


def _apply_vignette(img: Image.Image, strength: int = 165):
    width, height = img.size
    vignette = Image.new("L", (width, height), 0)
    draw = ImageDraw.Draw(vignette)

    for i in range(12):
        alpha = int(strength * (i / 12))
        inset_x = int(i * width * 0.025)
        inset_y = int(i * height * 0.025)
        draw.rounded_rectangle(
            (inset_x, inset_y, width - inset_x, height - inset_y),
            radius=80,
            outline=alpha,
            width=35,
        )

    vignette = vignette.filter(ImageFilter.GaussianBlur(50))
    dark = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    dark.putalpha(vignette)
    img.alpha_composite(dark)


def _apply_color_overlay(img: Image.Image, color=(255, 196, 0, 40)):
    layer = Image.new("RGBA", img.size, color)
    img.alpha_composite(layer)


def _build_dynamic_background(style: dict, size: Tuple[int, int]) -> Image.Image:
    width, height = size
    img = Image.new("RGBA", size, (10, 10, 10, 255))

    mode = style.get("bg_mode", "stadium_night")

    if mode == "stadium_night":
        _draw_vertical_gradient(img, (7, 14, 24), (18, 58, 30))
        _draw_crowd_band(img, int(height * 0.12), int(height * 0.34), theme="neutral")
        _draw_floodlights(img)
        _draw_pitch_lines(img, int(height * 0.63), color=(255, 255, 255, 50))
    elif mode == "breaking_red":
        _draw_vertical_gradient(img, (20, 4, 8), (80, 10, 18))
        _draw_crowd_band(img, int(height * 0.08), int(height * 0.38), theme="red")
        _draw_spotlight(img, (int(width * 0.25), int(height * 0.12)), 260, color=(255, 70, 70, 90))
        _draw_spotlight(img, (int(width * 0.75), int(height * 0.10)), 240, color=(255, 120, 120, 70))
    elif mode == "pitch":
        _draw_grass_texture(img, top_color=(18, 90, 36), bottom_color=(8, 45, 18))
        _draw_pitch_lines(img, int(height * 0.08), color=(255, 255, 255, 55))
        _draw_spotlight(img, (int(width * 0.50), int(height * 0.28)), 250, color=(255, 255, 210, 70))
    elif mode == "clean_blue_night":
        _draw_vertical_gradient(img, (12, 24, 46), (8, 14, 24))
        _draw_crowd_band(img, int(height * 0.15), int(height * 0.30), theme="neutral")
        _draw_spotlight(img, (int(width * 0.15), int(height * 0.12)), 220, color=(120, 180, 255, 75))
        _draw_spotlight(img, (int(width * 0.82), int(height * 0.12)), 240, color=(120, 180, 255, 60))
    elif mode == "crowd_fire":
        _draw_vertical_gradient(img, (30, 12, 8), (90, 35, 10))
        _draw_crowd_band(img, int(height * 0.10), int(height * 0.42), theme="red")
        _draw_spotlight(img, (int(width * 0.30), int(height * 0.18)), 280, color=(255, 110, 10, 95))
        _draw_spotlight(img, (int(width * 0.70), int(height * 0.15)), 250, color=(255, 165, 40, 75))
    elif mode == "emerald_gold":
        _draw_vertical_gradient(img, (6, 25, 18), (18, 75, 38))
        _draw_crowd_band(img, int(height * 0.10), int(height * 0.28), theme="neutral")
        _draw_floodlights(img)
        _apply_color_overlay(img, (255, 194, 78, 16))
    elif mode == "black_spotlight":
        _draw_vertical_gradient(img, (5, 5, 5), (24, 24, 24))
        _draw_spotlight(img, (int(width * 0.50), int(height * 0.20)), 280, color=(255, 255, 255, 70))
    elif mode == "stadium_flash":
        _draw_vertical_gradient(img, (6, 20, 35), (10, 68, 46))
        _draw_crowd_band(img, int(height * 0.12), int(height * 0.36), theme="neutral")
        _draw_floodlights(img)
        _draw_spotlight(img, (int(width * 0.50), int(height * 0.10)), 220, color=(0, 225, 255, 90))
    elif mode == "supporters_night":
        _draw_vertical_gradient(img, (20, 12, 36), (8, 10, 20))
        _draw_crowd_band(img, int(height * 0.08), int(height * 0.38), theme="purple")
        _draw_spotlight(img, (int(width * 0.18), int(height * 0.12)), 240, color=(170, 120, 255, 70))
        _draw_spotlight(img, (int(width * 0.82), int(height * 0.10)), 240, color=(170, 120, 255, 60))
    elif mode == "grass_ball":
        _draw_grass_texture(img, top_color=(20, 96, 42), bottom_color=(6, 45, 18))
        _draw_ball(img, (int(width * 0.52), int(height * 0.22)), 92)
        _draw_pitch_lines(img, int(height * 0.56), color=(255, 255, 255, 42))
    else:
        _draw_vertical_gradient(img, (10, 10, 10), (30, 30, 30))

    overlay_mode = style.get("overlay", "")
    if overlay_mode == "gold_glow":
        _apply_color_overlay(img, (255, 196, 78, 18))
    elif overlay_mode == "red_glow":
        _apply_color_overlay(img, (255, 0, 0, 16))
    elif overlay_mode == "green_glow":
        _apply_color_overlay(img, (40, 220, 90, 14))
    elif overlay_mode == "blue_glow":
        _apply_color_overlay(img, (40, 110, 255, 16))
    elif overlay_mode == "orange_glow":
        _apply_color_overlay(img, (255, 125, 30, 18))
    elif overlay_mode == "cyan_glow":
        _apply_color_overlay(img, (0, 225, 255, 15))
    elif overlay_mode == "purple_glow":
        _apply_color_overlay(img, (130, 80, 255, 18))
    elif overlay_mode == "white_glow":
        _apply_color_overlay(img, (255, 255, 255, 10))

    _add_noise_dots(img, 220, [(255, 255, 255, 12), (255, 220, 160, 10), (255, 255, 255, 8)], radius_range=(1, 2))
    _apply_vignette(img, strength=180)

    return img


def _load_base_canvas(style: dict) -> Image.Image:
    if os.path.exists(TEMPLATE_PATH):
        try:
            template = Image.open(TEMPLATE_PATH).convert("RGBA")
            template = template.resize(IMAGE_SIZE, Image.LANCZOS)
            generated = _build_dynamic_background(style, IMAGE_SIZE)
            generated.alpha_composite(template)
            return generated
        except Exception:
            pass

    return _build_dynamic_background(style, IMAGE_SIZE)


def _draw_top_badge(img: Image.Image, draw: ImageDraw.ImageDraw, style: dict, badge_text: str):
    width, height = img.size
    badge_font = _fit_font(draw, badge_text, style["headline_font"], 52, 32, int(width * 0.38), stroke_width=0)
    text_w, text_h = _text_size(draw, badge_text, badge_font, stroke_width=0)

    pad_x = 26
    pad_y = 14
    badge_w = text_w + pad_x * 2
    badge_h = text_h + pad_y * 2
    x1 = int((width - badge_w) / 2)
    y1 = int(height * 0.04)
    x2 = x1 + badge_w
    y2 = y1 + badge_h

    draw.rounded_rectangle((x1, y1, x2, y2), radius=22, fill=style["badge_fill"], outline=(255, 255, 255, 36), width=2)
    _draw_center_text(draw, width // 2, y1 + badge_h // 2 + 1, badge_text, badge_font, style["badge_text"], stroke_fill=(0, 0, 0), stroke_width=0)


def _draw_league(draw: ImageDraw.ImageDraw, style: dict, league_text: str, width: int, height: int):
    league_font = _fit_font(draw, league_text, style["league_font"], 42, 24, int(width * 0.82), stroke_width=2)
    league_lines = _wrap_text(draw, league_text, league_font, int(width * 0.82), stroke_width=2, max_lines=2)
    _draw_multiline_center(
        draw=draw,
        center_x=width // 2,
        top_y=int(height * 0.125),
        lines=league_lines,
        font=league_font,
        fill=style["league_fill"],
        stroke_fill=BLACK,
        stroke_width=2,
        spacing=4,
    )


def _draw_center_score_panel(img: Image.Image, draw: ImageDraw.ImageDraw, style: dict, minute_text: str, score_text: str):
    width, height = img.size

    panel_w = int(width * 0.36)
    panel_h = int(height * 0.18)
    x1 = int((width - panel_w) / 2)
    y1 = int(height * 0.26)
    x2 = x1 + panel_w
    y2 = y1 + panel_h

    panel_fill = (0, 0, 0, 120) if style["name"] != "goal_alert_red" else (90, 10, 18, 125)
    accent = style.get("accent_line", GOLD)

    glass = Image.new("RGBA", img.size, (0, 0, 0, 0))
    glass_draw = ImageDraw.Draw(glass, "RGBA")
    glass_draw.rounded_rectangle((x1, y1, x2, y2), radius=30, fill=panel_fill, outline=(255, 255, 255, 40), width=2)
    glass_draw.rounded_rectangle((x1 + 10, y1 + 10, x2 - 10, y1 + 22), radius=8, fill=(255, 255, 255, 22))
    img.alpha_composite(glass)

    draw.rounded_rectangle((x1, y1 - 10, x2, y1 - 2), radius=4, fill=accent)
    draw.rounded_rectangle((x1, y2 + 2, x2, y2 + 10), radius=4, fill=accent)

    minute_font = _fit_font(draw, minute_text, "montserrat_bold", 34, 22, int(panel_w * 0.80), stroke_width=2)
    score_font = _fit_font(draw, score_text, style["score_font"], 120, 72, int(panel_w * 0.84), stroke_width=4)

    _draw_center_text(draw, width // 2, y1 + int(panel_h * 0.28), minute_text, minute_font, style["minute_fill"], stroke_fill=BLACK, stroke_width=2)
    _draw_center_text(draw, width // 2, y1 + int(panel_h * 0.72), score_text, score_font, style["score_fill"], stroke_fill=style["score_stroke"], stroke_width=4)


def _draw_logos_and_teams(img: Image.Image, draw: ImageDraw.ImageDraw, style: dict, home_text: str, away_text: str, home_logo, away_logo):
    width, height = img.size

    logo_box = (190, 190)
    home_x = int(width * 0.15)
    away_x = int(width * 0.85)
    logos_y = int(height * 0.44)

    home_logo = home_logo if home_logo is not None else None
    away_logo = away_logo if away_logo is not None else None

    for center_x in [home_x, away_x]:
        shadow = Image.new("RGBA", img.size, (0, 0, 0, 0))
        shadow_draw = ImageDraw.Draw(shadow, "RGBA")
        shadow_draw.ellipse((center_x - 92, logos_y - 82, center_x + 92, logos_y + 102), fill=(0, 0, 0, 70))
        shadow = shadow.filter(ImageFilter.GaussianBlur(16))
        img.alpha_composite(shadow)

    if home_logo is not None:
        img.paste(home_logo, (home_x - home_logo.width // 2, logos_y - home_logo.height // 2), home_logo)

    if away_logo is not None:
        img.paste(away_logo, (away_x - away_logo.width // 2, logos_y - away_logo.height // 2), away_logo)

    team_font_home = _fit_font(draw, home_text, style["team_font"], 50, 26, int(width * 0.30), stroke_width=2)
    team_font_away = _fit_font(draw, away_text, style["team_font"], 50, 26, int(width * 0.30), stroke_width=2)

    home_lines = _wrap_text(draw, home_text, team_font_home, int(width * 0.30), stroke_width=2, max_lines=2)
    away_lines = _wrap_text(draw, away_text, team_font_away, int(width * 0.30), stroke_width=2, max_lines=2)

    _draw_multiline_center(
        draw=draw,
        center_x=home_x,
        top_y=int(height * 0.60),
        lines=home_lines,
        font=team_font_home,
        fill=style["team_fill"],
        stroke_fill=BLACK,
        stroke_width=2,
        spacing=3,
    )
    _draw_multiline_center(
        draw=draw,
        center_x=away_x,
        top_y=int(height * 0.60),
        lines=away_lines,
        font=team_font_away,
        fill=style["team_fill"],
        stroke_fill=BLACK,
        stroke_width=2,
        spacing=3,
    )

    vs_font = _load_font(style["headline_font"], 56)
    _draw_center_text(draw, width // 2, int(height * 0.51), "VS", vs_font, style["badge_text"], stroke_fill=BLACK, stroke_width=2)


def _draw_pick_box(img: Image.Image, draw: ImageDraw.ImageDraw, style: dict, pick_text: str):
    width, height = img.size
    box_w = int(width * 0.78)
    box_h = int(height * 0.16)
    x1 = int((width - box_w) / 2)
    y1 = int(height * 0.77)
    x2 = x1 + box_w
    y2 = y1 + box_h

    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    layer_draw = ImageDraw.Draw(layer, "RGBA")
    layer_draw.rounded_rectangle((x1, y1, x2, y2), radius=34, fill=style["pick_box"], outline=(255, 255, 255, 44), width=2)
    layer_draw.rounded_rectangle((x1 + 16, y1 + 14, x2 - 16, y1 + 24), radius=8, fill=(255, 255, 255, 22))
    img.alpha_composite(layer)

    pick_font = _fit_font(draw, pick_text, style["pick_font"], 70, 34, int(box_w * 0.86), stroke_width=3)
    pick_lines = _wrap_text(draw, pick_text, pick_font, int(box_w * 0.86), stroke_width=3, max_lines=2)

    badge_font = _load_font("montserrat_bold", 24)
    mini_badge = "LIVE EDGE"
    text_w, text_h = _text_size(draw, mini_badge, badge_font, stroke_width=0)
    bx1 = x1 + 20
    by1 = y1 - 22
    bx2 = bx1 + text_w + 24
    by2 = by1 + text_h + 14
    draw.rounded_rectangle((bx1, by1, bx2, by2), radius=15, fill=style["accent_line"])
    _draw_center_text(draw, (bx1 + bx2) // 2, (by1 + by2) // 2 + 1, mini_badge, badge_font, WHITE, stroke_fill=BLACK, stroke_width=0)

    _draw_multiline_center(
        draw=draw,
        center_x=width // 2,
        top_y=y1 + 34,
        lines=pick_lines,
        font=pick_font,
        fill=style["pick_fill"],
        stroke_fill=BLACK,
        stroke_width=3,
        spacing=2,
    )


def _decorate_with_subtle_lines(draw: ImageDraw.ImageDraw, style: dict, width: int, height: int):
    accent = style.get("accent_line", GOLD)
    alpha_color = (accent[0], accent[1], accent[2], 90) if isinstance(accent, tuple) and len(accent) == 3 else accent

    try:
        draw.arc((int(width * 0.05), int(height * 0.18), int(width * 0.23), int(height * 0.36)), 250, 20, fill=alpha_color, width=4)
        draw.arc((int(width * 0.77), int(height * 0.18), int(width * 0.95), int(height * 0.36)), 160, 290, fill=alpha_color, width=4)
        draw.line((int(width * 0.16), int(height * 0.73), int(width * 0.32), int(height * 0.73)), fill=alpha_color, width=3)
        draw.line((int(width * 0.68), int(height * 0.73), int(width * 0.84), int(height * 0.73)), fill=alpha_color, width=3)
    except Exception:
        pass


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
    include_pick: bool = True,
):
    style = random.choice(STYLE_PRESETS)
    img = _load_base_canvas(style)
    draw = ImageDraw.Draw(img, "RGBA")

    width, height = img.size
    print(f"[ALERT IMAGE] style={style['name']} | size={img.size} | include_pick={include_pick}")

    league_text = _safe_text(league).upper()
    home_text = _safe_text(home).upper()
    away_text = _safe_text(away).upper()
    score_text = _safe_text(score)
    minute_value = _safe_text(minute)
    minute_text = f"MIN {minute_value}'" if minute_value else "LIVE NOW"
    pick_text = _safe_text(pick).upper()

    badge_variants = ["GOAL ALERT", "LIVE ALERT", "LIVE SIGNAL", "MATCH ALERT", "WATCH NOW"]
    badge_text = random.choice(badge_variants)

    _draw_top_badge(img, draw, style, badge_text)
    _draw_league(draw, style, league_text, width, height)
    _draw_center_score_panel(img, draw, style, minute_text, score_text)

    logo_size = (190, 190)
    home_logo = _download_logo(home_logo_url, logo_size)
    away_logo = _download_logo(away_logo_url, logo_size)

    _draw_logos_and_teams(img, draw, style, home_text, away_text, home_logo, away_logo)

    if include_pick and pick_text:
        _draw_pick_box(img, draw, style, pick_text)

    _decorate_with_subtle_lines(draw, style, width, height)

    filename = f"/tmp/alert_{int(time.time())}_{random.randint(1000, 9999)}.jpg"
    img.convert("RGB").save(filename, "JPEG", quality=95, optimize=True)

    print(f"[ALERT IMAGE] Saved to {filename}")
    return filename
