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
    # MILESTONE VALUE
    # =========================
    # folosim date_text ca valoare (ex: "100x")
    milestone_value = str(date_text)

    # =========================
    # POSITION (CENTER)
    # =========================
    center_x = int(w * 0.50)
    center_y = int(h * 0.52)

    # =========================
    # DRAW MILESTONE
    # =========================
    draw_text(
        base_img=img,
        draw=draw,
        x=center_x,
        y=center_y,
        text=milestone_value,
        size=int(h * 0.11),
        fill=white,
        stroke_fill=black,
        bold=True,
        anchor="mm",
    )

    filename = f"/tmp/milestone_{int(time.time())}.jpg"
    img.convert("RGB").save(filename, "JPEG", quality=95)

    print(f"[MILESTONE IMAGE] Saved to {filename}")
    return filename
