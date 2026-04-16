import os
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FONTS_DIR = os.path.join(BASE_DIR, "fonts")


def get_truetype_font(size: int, bold: bool = False):
    repo_candidates = [
        os.path.join(FONTS_DIR, "Heart Bubble.otf"),
    ]

    for candidate in repo_candidates:
        if os.path.exists(candidate):
            try:
                font = ImageFont.truetype(candidate, size=size)
                print(f"[FONT] Using repo font: {candidate} | size={size}")
                return font
            except Exception as e:
                print(f"[FONT] Failed repo font: {candidate} | {e}")

    # fallback fonts (Linux Railway safe)
    local_candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]

    for candidate in local_candidates:
        try:
            font = ImageFont.truetype(candidate, size=size)
            print(f"[FONT] Using fallback font: {candidate}")
            return font
        except Exception:
            pass

    print("[FONT] No font found, using default")
    return None


def draw_text(
    base_img,
    draw,
    x: int,
    y: int,
    text: str,
    size: int,
    fill=(255, 255, 255),
    stroke_fill=(0, 0, 0),
    bold: bool = True,
    anchor: str = "lt",
):
    font = get_truetype_font(size=size, bold=bold)

    if font:
        draw.text(
            (x, y),
            str(text),
            fill=fill,
            anchor=anchor,
            font=font,
            stroke_width=max(2, int(size * 0.06)),
            stroke_fill=stroke_fill,
        )
    else:
        # fallback basic (rare case)
        default_font = ImageFont.load_default()
        draw.text(
            (x, y),
            str(text),
            fill=fill,
            anchor=anchor,
            font=default_font,
        )
