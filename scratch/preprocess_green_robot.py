"""Pre-process green robot sprite sheet into individual transparent PNG frames for fast loading"""
from PIL import Image
import os

img_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "unnamed (2).jpg")
out_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

img = Image.open(img_path).convert("RGBA")
w, h = img.size
cols, rows = 6, 4
fw, fh = w // cols, h // rows

def is_green_bg(r, g, b):
    """Neon green background removal - preserves olive/military green robot"""
    if g < 100:
        return False
    green_ratio = g / max(1, max(r, b))
    avg_rb = (r + b) / 2
    if green_ratio > 1.6 and g > 140 and avg_rb < 130:
        return True
    if g > 170 and r < 150 and b < 100 and green_ratio > 1.3:
        return True
    return False

# Create combined transparent sprite sheet
result = Image.new("RGBA", (fw * cols, fh * rows), (0, 0, 0, 0))

for row in range(rows):
    for col in range(cols):
        x0, y0 = col * fw, row * fh
        for py in range(fh):
            for px in range(fw):
                r, g, b = img.getpixel((x0 + px, y0 + py))[:3]
                if not is_green_bg(r, g, b):
                    result.putpixel((x0 + px, y0 + py), (r, g, b, 255))

# Save as PNG with transparency
out_path = os.path.join(out_dir, "green_robot_sheet.png")
result.save(out_path)
print(f"Saved {out_path}")
print(f"Size: {os.path.getsize(out_path)} bytes")
