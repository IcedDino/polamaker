import io
import json
from typing import List

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from PIL import Image, ImageDraw, ImageFont

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://polamaker.floresr.com"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DPI = 300

# Canvas sizes in inches (width, height) — always portrait, we flip for landscape
PAPER_SIZES = {
    "a4":     (8.27, 11.69),
    "letter": (8.5,  11.0),
}

# Polaroid sizes in inches (frame_w, frame_h, photo_w, photo_h)
# Frame includes the white border; photo is the image area inside
POLAROID_SIZES = {
    "tall":   (2.13, 2.76, 1.89, 1.89),  # 54x70mm, square photo area
    "venti":  (2.13, 2.44, 1.89, 1.89),  # 54x62mm, less bottom margin
    "grande": (2.76, 2.44, 2.52, 1.77),  # 70x62mm, wide landscape photo
}


def in_to_px(inches: float) -> int:
    return int(inches * DPI)


def create_polaroid_layout(
    images=None,
    paper="letter",
    orientation="portrait",
    polaroid="tall",
    custom_w=8.5,
    custom_h=11.0,
    add_numbers=False,
):
    # --- Canvas dimensions ---
    if paper == "custom":
        cw_in, ch_in = custom_w, custom_h
    else:
        cw_in, ch_in = PAPER_SIZES.get(paper, PAPER_SIZES["letter"])

    if orientation == "landscape":
        cw_in, ch_in = ch_in, cw_in

    canvas_w = in_to_px(cw_in)
    canvas_h = in_to_px(ch_in)

    # --- Polaroid dimensions ---
    pol_w_in, pol_h_in, photo_w_in, photo_h_in = POLAROID_SIZES.get(polaroid, POLAROID_SIZES["tall"])
    pol_w = in_to_px(pol_w_in)
    pol_h = in_to_px(pol_h_in)
    photo_w = in_to_px(photo_w_in)
    photo_h = in_to_px(photo_h_in)

    # --- Grid layout: fit as many polaroids as possible ---
    cols = max(1, canvas_w // pol_w)
    rows = max(1, canvas_h // pol_h)

    # Cap at 9 total slots
    while cols * rows > 9:
        if cols >= rows:
            cols -= 1
        else:
            rows -= 1
    cols = max(1, cols)
    rows = max(1, rows)

    # Even spacing
    x_gap = (canvas_w - cols * pol_w) // (cols + 1)
    y_gap = (canvas_h - rows * pol_h) // (rows + 1)

    # Photo offset within polaroid frame (centered horizontally, upper portion)
    photo_x_offset = (pol_w - photo_w) // 2
    photo_y_offset = (pol_w - photo_w) // 2  # equal top/side padding, bottom is caption area

    # --- Draw ---
    canvas = Image.new("RGB", (canvas_w, canvas_h), "white")
    draw = ImageDraw.Draw(canvas)

    try:
        font = ImageFont.truetype("arial.ttf", 36)
        font_small = ImageFont.truetype("arial.ttf", 22)
    except:
        font = ImageFont.load_default()
        font_small = font

    images = images or []

    for row in range(rows):
        for col in range(cols):
            idx = row * cols + col

            x0 = x_gap + col * (pol_w + x_gap)
            y0 = y_gap + row * (pol_h + y_gap)
            x1 = x0 + pol_w
            y1 = y0 + pol_h

            # Polaroid frame — clean white card with precise border
            draw.rectangle([x0, y0, x1, y1], fill="white")
            # Outer border — fine 1px ink line
            draw.rectangle([x0, y0, x1, y1], outline="#1a1a18", width=2)
            # Inner border line — gives the frame depth and quality feel
            inset = 5
            draw.rectangle([x0 + inset, y0 + inset, x1 - inset, y1 - inset], outline="#e8e8e4", width=1)

            # Photo area bounds
            px0 = x0 + photo_x_offset
            py0 = y0 + photo_y_offset
            px1 = px0 + photo_w
            py1 = py0 + photo_h

            if idx < len(images):
                img = images[idx].copy()

                # Crop to fill photo area (cover, not fit)
                target_ratio = photo_w / photo_h
                iw, ih = img.size
                src_ratio = iw / ih

                if src_ratio > target_ratio:
                    # wider than target — crop sides
                    new_w = int(ih * target_ratio)
                    left = (iw - new_w) // 2
                    img = img.crop((left, 0, left + new_w, ih))
                else:
                    # taller than target — crop top/bottom
                    new_h = int(iw / target_ratio)
                    top = (ih - new_h) // 2
                    img = img.crop((0, top, iw, top + new_h))

                img = img.resize((photo_w, photo_h), Image.LANCZOS)

                if img.mode == "RGBA":
                    img = img.convert("RGB")

                canvas.paste(img, (px0, py0))
            else:
                # Clean placeholder — linen texture feel
                draw.rectangle([px0, py0, px1, py1], fill="#f0ede8")
                # Subtle crosshair
                mid_x = (px0 + px1) // 2
                mid_y = (py0 + py1) // 2
                line_len = min(photo_w, photo_h) // 8
                draw.line([mid_x - line_len, mid_y, mid_x + line_len, mid_y], fill="#c8c4bc", width=2)
                draw.line([mid_x, mid_y - line_len, mid_x, mid_y + line_len], fill="#c8c4bc", width=2)
                draw.ellipse([mid_x - line_len//2, mid_y - line_len//2,
                              mid_x + line_len//2, mid_y + line_len//2],
                             outline="#c8c4bc", width=2)

            # Thin border around photo area
            draw.rectangle([px0 - 1, py0 - 1, px1 + 1, py1 + 1], outline="#e0ddd8", width=1)

            # Caption area — small decorative line in footer
            cap_y = py1 + (y1 - py1) // 2
            line_w = pol_w // 4
            line_x0 = x0 + (pol_w - line_w) // 2
            draw.line([line_x0, cap_y, line_x0 + line_w, cap_y], fill="#d8d5d0", width=2)

            # Number label
            if add_numbers:
                label = str(idx + 1)
                text_w = draw.textlength(label, font=font)
                text_x = x0 + (pol_w - text_w) // 2
                text_y = py1 + (y1 - py1 - 36) // 2
                draw.text((text_x, text_y), label, fill="#aaa", font=font)

    # Watermark — bottom right, very subtle
    try:
        wm_font = ImageFont.truetype("arial.ttf", 28)
    except:
        wm_font = font_small
    wm_text = "polamaker.floresr.com"
    wm_w = draw.textlength(wm_text, font=wm_font)
    draw.text(
        (canvas_w - wm_w - 40, canvas_h - 48),
        wm_text,
        fill="#c8c4bc",
        font=wm_font
    )

    return canvas


@app.post("/generate")
async def generate_polaroid(
    config: str = Form(...),
    images: List[UploadFile] = File(default=[]),
):
    cfg = json.loads(config)

    imgs = []
    for file in images[:9]:
        contents = await file.read()
        if len(contents) > 10 * 1024 * 1024:
            return {"error": f"{file.filename} is too large (max 10MB each)"}
        img = Image.open(io.BytesIO(contents))
        imgs.append(img)

    result = create_polaroid_layout(
        images=imgs,
        paper=cfg.get("paper", "letter"),
        orientation=cfg.get("orientation", "portrait"),
        polaroid=cfg.get("polaroid", "tall"),
        custom_w=cfg.get("custom_w", 8.5),
        custom_h=cfg.get("custom_h", 11.0),
        add_numbers=cfg.get("add_numbers", False),
    )

    buf = io.BytesIO()
    result.save(buf, format="PNG", dpi=(DPI, DPI))
    buf.seek(0)
    return StreamingResponse(buf, media_type="image/png")
