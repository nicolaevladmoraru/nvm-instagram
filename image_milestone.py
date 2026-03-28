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

    gold = (242, 196, 78)
    white = (255, 255, 255)
    black = (0, 0, 0)

    center_x = int(w * 0.50)

    header_text = str(title or "NVM MILESTONE").strip()
    if not header_text:
        header_text = "NVM MILESTONE"

    milestone_text = str(date_text or "").strip()
    if not milestone_text:
        milestone_text = "100X"

    subtitle_text = "PROFIT MILESTONE"

    title_size = int(h * 0.052)
    milestone_size = int(h * 0.135)
    subtitle_size = int(h * 0.034)

    title_fallback_h = int(h * 0.056)
    milestone_fallback_h = int(h * 0.140)
    subtitle_fallback_h = int(h * 0.038)

    draw_text(
        base_img=img,
        draw=draw,
        x=center_x,
        y=int(h * 0.085),
        text=header_text,
        size=title_size,
        fill=gold,
        stroke_fill=black,
        bold=True,
        anchor="mm",
        fallback_height=title_fallback_h,
    )

    draw_text(
        base_img=img,
        draw=draw,
        x=center_x,
        y=int(h * 0.47),
        text=milestone_text,
        size=milestone_size,
        fill=white,
        stroke_fill=black,
        bold=True,
        anchor="mm",
        fallback_height=milestone_fallback_h,
    )

    draw_text(
        base_img=img,
        draw=draw,
        x=center_x,
        y=int(h * 0.62),
        text=subtitle_text,
        size=subtitle_size,
        fill=gold,
        stroke_fill=black,
        bold=True,
        anchor="mm",
        fallback_height=subtitle_fallback_h,
    )

    filename = f"/tmp/milestone_report_{int(time.time())}.jpg"
    img.convert("RGB").save(filename, "JPEG", quality=95)
    print(f"[MILESTONE IMAGE] Saved to {filename} | final_size={img.size}")
    return filename
