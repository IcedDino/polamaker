from generate import create_polaroid_layout

# Simple example: Create a layout using the default settings
create_polaroid_layout()

# Complete example: Create a layout with your own images
create_polaroid_layout(
    image_folder="photos",  # Folder containing your images
    output_filename="my_polaroid_layout",  # Output filename (without extension)
    add_numbers=False,  # No numbers on polaroids
    add_photo_frames=False  # No black frames around photos
)

"""
Additional customization options:

1. Resize or crop your input images beforehand for better control
   - You can use libraries like PIL or OpenCV to prepare your images

2. Batch processing multiple folders:
   import os

   folders = ["vacation_photos", "birthday_party", "family_reunion"]
   for folder in folders:
       output_name = f"polaroids_{os.path.basename(folder)}"
       create_polaroid_layout(folder, output_name)

3. Creating layouts with different numbers of images:
   - The function currently creates a 3x3 grid (9 polaroids)
   - If you provide fewer than 9 images, empty placeholders will be shown
   - If you provide more than 9 images, only the first 9 will be used
   - To use more images, you would need to create multiple pages

4. Adding captions:
   - The current implementation adds numbers to each polaroid
   - To add custom captions, modify the code to accept a list of captions
"""