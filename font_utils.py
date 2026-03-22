import os
from PIL import Image, ImageDraw, ImageFont


def get_truetype_font(size: int, bold: bool = False):
    repo_candidates = [
        "fonts/Heart Bubble.otf",
    ]

    for candidate in repo_candidates:
        if os.path.exists(candidate):
            try:
                font = ImageFont.truetype(candidate, size=size)
                print(f"[FONT] Using repo font: {candidate} | size={size}")
                return font
            except Exception as e:
                print(f"[FONT] Failed repo font: {candidate} | {e}")

    local_candidates = []
    if bold:
        local_candidates = [
            "DejaVuSans-Bold.ttf",
            "DejaVuSans.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
        ]
    else:
        local_candidates = [
            "DejaVuSans.ttf",
            "DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
        ]

    for candidate in local_candidates:
        try:
            font = ImageFont.truetype(candidate, size=size)
            print(f"[FONT] Using local font: {candidate} | size={size} | bold={bold}")
            return font
        except Exception as e:
            print(f"[FONT] Failed local: {candidate} | {e}")

    print(f"[FONT] No truetype font found | size={size} | bold={bold}")
    return None


def text_size(draw: ImageDraw.ImageDraw, text: str, font) -> tuple[int, int]:
    bbox = draw.textbbox((0, 0), str(text), font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def wrap_text_by_pixels(draw: ImageDraw.ImageDraw, text: str, font, max_width: int):
    words = str(text or "").split()
    if not words:
        return [""]

    lines = []
    current = words[0]

    for word in words[1:]:
        test = current + " " + word
        w, _ = text_size(draw, test, font)
        if w <= max_width:
            current = test
        else:
            lines.append(current)
            current = word

    lines.append(current)
    return lines


def draw_scaled_bitmap_text(
    base_img,
    x: int,
    y: int,
    text: str,
    target_height: int,
    fill=(255, 255, 255),
    stroke_fill=(0, 0, 0),
    anchor: str = "lt",
):
    default_font = ImageFont.load_default()

    temp_img = Image.new("RGBA", (4000, 1400), (0, 0, 0, 0))
    temp_draw = ImageDraw.Draw(temp_img)

    stroke_offsets = [
        (-3, -3), (-3, 0), (-3, 3),
        (0, -3),           (0, 3),
        (3, -3),  (3, 0),  (3, 3),
    ]

    for dx, dy in stroke_offsets:
        temp_draw.text((30 + dx, 30 + dy), str(text), font=default_font, fill=stroke_fill)

    temp_draw.text((30, 30), str(text), font=default_font, fill=fill)

    bbox = temp_img.getbbox()
    if not bbox:
        return

    cropped = temp_img.crop(bbox)
    cw, ch = cropped.size
    if ch <= 0:
        return

    scale = max(1, int(target_height / ch))
    enlarged = cropped.resize((cw * scale, ch * scale), Image.Resampling.BICUBIC)

    ew, eh = enlarged.size

    if anchor == "mm":
        px = int(x - ew / 2)
        py = int(y - eh / 2)
    elif anchor == "lm":
        px = int(x)
        py = int(y - eh / 2)
    else:
        px = int(x)
        py = int(y)

    base_img.alpha_composite(enlarged, (px, py))


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
    fallback_height: int | None = None,
):
    font = get_truetype_font(size=size, bold=bold)

    if font is not None:
        draw.text(
            (x, y),
            str(text),
            fill=fill,
            anchor=anchor,
            font=font,
            stroke_width=max(2, int(size * 0.06)),
            stroke_fill=stroke_fill,
        )
        return font

    draw_scaled_bitmap_text(
        base_img=base_img,
        x=x,
        y=y,
        text=text,
        target_height=fallback_height or size,
        fill=fill,
        stroke_fill=stroke_fill,
        anchor=anchor,
    )
    return ImageFont.load_default()
