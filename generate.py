from PIL import Image, ImageDraw, ImageFont
import os
import glob


def create_polaroid_layout(image_folder=None, output_filename="polaroid_layout", add_numbers=False,
                           add_photo_frames=False):
    """
    Create a polaroid layout with either loaded images or placeholder rectangles.

    Args:
        image_folder (str): Path to folder containing images to use
        output_filename (str): Base name for output files (without extension)
        add_numbers (bool): Whether to add numbers to the polaroids (default: False)
        add_photo_frames (bool): Whether to add black frames around photos (default: False)

    Returns:
        PIL.Image: The created canvas with polaroid layout
    """
    # Constants
    DPI = 300
    LETTER_WIDTH_IN = 8.5  # Standard letter in portrait orientation
    LETTER_HEIGHT_IN = 11
    canvas_width = int(LETTER_WIDTH_IN * DPI)
    canvas_height = int(LETTER_HEIGHT_IN * DPI)

    # Polaroid and photo sizes in inches
    polaroid_w_in = 2.8
    polaroid_h_in = 3.4
    photo_size_in = 2.4

    # Convert sizes to pixels
    polaroid_w = int(polaroid_w_in * DPI)
    polaroid_h = int(polaroid_h_in * DPI)
    photo_size = int(photo_size_in * DPI)

    # Layout - 3×3 grid (9 polaroids)
    cols, rows = 3, 3
    x_spacing = (canvas_width - cols * polaroid_w) // (cols + 1)
    y_spacing = (canvas_height - rows * polaroid_h) // (rows + 1)

    # Extra white space below photo: about 0.6"
    bottom_margin = int(0.6 * DPI)
    top_padding = (polaroid_h - bottom_margin - photo_size) // 2

    # Create canvas
    canvas = Image.new("RGB", (canvas_width, canvas_height), "white")
    draw = ImageDraw.Draw(canvas)

    # Try to load a font for the labels
    try:
        font = ImageFont.truetype("Arial.ttf", 24)  # Adjust font size as needed
    except IOError:
        # Fallback to default font
        font = ImageFont.load_default()

    # Load images if a folder is provided
    images = []
    if image_folder and os.path.isdir(image_folder):
        # Look for common image formats
        image_patterns = ['*.jpg', '*.jpeg', '*.png', '*.gif', '*.bmp', '*.tiff']
        for pattern in image_patterns:
            images.extend(glob.glob(os.path.join(image_folder, pattern)))

        print(f"Found {len(images)} images in {image_folder}")

    # Draw grid lines for reference (optional)
    draw_grid = False
    if draw_grid:
        for i in range(cols + 1):
            x = x_spacing + i * (polaroid_w + x_spacing) - x_spacing // 2
            draw.line([(x, 0), (x, canvas_height)], fill="lightblue", width=1)
        for i in range(rows + 1):
            y = y_spacing + i * (polaroid_h + y_spacing) - y_spacing // 2
            draw.line([(0, y), (canvas_width, y)], fill="lightblue", width=1)

    for row in range(rows):
        for col in range(cols):
            # Calculate polaroid position
            x0 = x_spacing + col * (polaroid_w + x_spacing)
            y0 = y_spacing + row * (polaroid_h + y_spacing)
            x1 = x0 + polaroid_w
            y1 = y0 + polaroid_h

            # Photo area position
            photo_x0 = x0 + (polaroid_w - photo_size) // 2
            photo_y0 = y0 + top_padding
            photo_x1 = photo_x0 + photo_size
            photo_y1 = photo_y0 + photo_size

            # Draw polaroid frame
            draw.rectangle([x0, y0, x1, y1], fill="white", outline="lightgray", width=3)

            # Get image index
            img_idx = row * cols + col

            # Try to use an actual image if available
            if images and img_idx < len(images):
                try:
                    # Open and resize image to fit the photo area
                    img = Image.open(images[img_idx])

                    # Resize image to fit the photo area while preserving aspect ratio
                    img_w, img_h = img.size
                    aspect_ratio = img_w / img_h

                    if aspect_ratio > 1:  # Landscape orientation
                        new_w = photo_size
                        new_h = int(new_w / aspect_ratio)
                    else:  # Portrait or square orientation
                        new_h = photo_size
                        new_w = int(new_h * aspect_ratio)

                    img = img.resize((new_w, new_h), Image.LANCZOS)

                    # Center the image in the photo area
                    paste_x = photo_x0 + (photo_size - new_w) // 2
                    paste_y = photo_y0 + (photo_size - new_h) // 2

                    # Create a background for transparency support
                    if img.mode == 'RGBA':
                        bg = Image.new('RGBA', img.size, (255, 255, 255, 255))
                        img = Image.alpha_composite(bg, img)

                    # Paste the image onto the canvas
                    canvas.paste(img, (paste_x, paste_y))

                    # Draw border around the photo only if requested
                    if add_photo_frames:
                        draw.rectangle([photo_x0, photo_y0, photo_x1, photo_y1], outline="black", width=2, fill=None)

                except Exception as e:
                    print(f"Error processing image {images[img_idx]}: {e}")
                    # Fall back to placeholder - without black frame
                    draw.rectangle([photo_x0, photo_y0, photo_x1, photo_y1], fill="lightgray", outline=None)
            else:
                # No image available, draw placeholder without the black frame
                draw.rectangle([photo_x0, photo_y0, photo_x1, photo_y1], fill="lightgray", outline=None)

            # Add a small label with polaroid number if requested (turned off by default)
            if add_numbers:
                polaroid_num = img_idx + 1
                # Calculate position for centered text
                text = f"{polaroid_num}"
                text_width = draw.textlength(text, font=font) if hasattr(draw, 'textlength') else font.getsize(text)[0]
                text_x = x0 + (polaroid_w - text_width) // 2
                text_y = y1 - bottom_margin // 2 - 12  # Adjust vertical position

                draw.text((text_x, text_y), text, fill="black", font=font)

    # Save output
    canvas.save(f"{output_filename}.png", "PNG")
    try:
        canvas.save(f"{output_filename}.pdf", "PDF")
    except Exception as e:
        print(f"Couldn't save PDF (this requires additional libraries): {e}")

    # Show optimal layout information
    print(f"Letter page size: {LETTER_WIDTH_IN}\" × {LETTER_HEIGHT_IN}\" (portrait)")
    print(f"Polaroid size: {polaroid_w_in}\" × {polaroid_h_in}\"")
    print(f"Layout: {cols} columns × {rows} rows = {cols * rows} polaroids")
    print(f"Horizontal spacing: {x_spacing / DPI:.2f}\"")
    print(f"Vertical spacing: {y_spacing / DPI:.2f}\"")

    return canvas


# Example usage:
if __name__ == "__main__":
    # To use with images from a folder:
    # create_polaroid_layout("path/to/your/images", "my_polaroids")

    # To use with placeholder rectangles:
    create_polaroid_layout(output_filename="polaroid_template_9up_portrait")