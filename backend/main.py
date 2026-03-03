from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from PIL import Image, ImageDraw, ImageFont
from typing import List
import io

app = FastAPI()


def create_polaroid_layout(images=None, add_numbers=False, add_photo_frames=False):
    DPI = 300
    LETTER_WIDTH_IN = 8.5
    LETTER_HEIGHT_IN = 11

    canvas_width = int(LETTER_WIDTH_IN * DPI)
    canvas_height = int(LETTER_HEIGHT_IN * DPI)

    polaroid_w = int(2.8 * DPI)
    polaroid_h = int(3.4 * DPI)
    photo_size = int(2.4 * DPI)

    cols, rows = 3, 3
    x_spacing = (canvas_width - cols * polaroid_w) // (cols + 1)
    y_spacing = (canvas_height - rows * polaroid_h) // (rows + 1)

    bottom_margin = int(0.6 * DPI)
    top_padding = (polaroid_h - bottom_margin - photo_size) // 2

    canvas = Image.new("RGB", (canvas_width, canvas_height), "white")
    draw = ImageDraw.Draw(canvas)

    try:
        font = ImageFont.truetype("arial.ttf", 24)
    except:
        font = ImageFont.load_default()

    images = images or []

    for row in range(rows):
        for col in range(cols):
            x0 = x_spacing + col * (polaroid_w + x_spacing)
            y0 = y_spacing + row * (polaroid_h + y_spacing)
            x1 = x0 + polaroid_w
            y1 = y0 + polaroid_h

            photo_x0 = x0 + (polaroid_w - photo_size) // 2
            photo_y0 = y0 + top_padding
            photo_x1 = photo_x0 + photo_size
            photo_y1 = photo_y0 + photo_size

            draw.rectangle([x0, y0, x1, y1], fill="white", outline="lightgray", width=3)

            img_idx = row * cols + col

            if img_idx < len(images):
                img = images[img_idx]

                img_w, img_h = img.size
                aspect_ratio = img_w / img_h

                if aspect_ratio > 1:
                    new_w = photo_size
                    new_h = int(new_w / aspect_ratio)
                else:
                    new_h = photo_size
                    new_w = int(new_h * aspect_ratio)

                img = img.resize((new_w, new_h), Image.LANCZOS)

                paste_x = photo_x0 + (photo_size - new_w) // 2
                paste_y = photo_y0 + (photo_size - new_h) // 2

                if img.mode == "RGBA":
                    img = img.convert("RGB")

                canvas.paste(img, (paste_x, paste_y))

                if add_photo_frames:
                    draw.rectangle(
                        [photo_x0, photo_y0, photo_x1, photo_y1],
                        outline="black",
                        width=2,
                    )
            else:
                draw.rectangle(
                    [photo_x0, photo_y0, photo_x1, photo_y1],
                    fill="lightgray",
                )

            if add_numbers:
                text = str(img_idx + 1)
                text_width = draw.textlength(text, font=font)
                text_x = x0 + (polaroid_w - text_width) // 2
                text_y = y1 - bottom_margin // 2 - 12
                draw.text((text_x, text_y), text, fill="black", font=font)

    return canvas


@app.post("/generate")
async def generate_polaroid(
    files: List[UploadFile] = File(...),
    add_numbers: bool = Form(False),
    add_photo_frames: bool = Form(False),
):
    images = []

    for file in files[:9]:  # Limit to 9 max
        contents = await file.read()

        if len(contents) > 5 * 1024 * 1024:
            return {"error": "File too large (max 5MB each)"}

        img = Image.open(io.BytesIO(contents))
        images.append(img)

    result_image = create_polaroid_layout(
        images=images,
        add_numbers=add_numbers,
        add_photo_frames=add_photo_frames,
    )

    img_bytes = io.BytesIO()
    result_image.save(img_bytes, format="PNG")
    img_bytes.seek(0)

    return StreamingResponse(img_bytes, media_type="image/png")
