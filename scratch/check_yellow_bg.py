from PIL import Image
import os

img_path = "robotvang.png"
if os.path.exists(img_path):
    img = Image.open(img_path).convert("RGBA")
    w, h = img.size
    cols, rows = 6, 4
    fw, fh = w // cols, h // rows
    print(f"Image size: {w}x{h}, Frame size: {fw}x{fh}")
    
    # Check pixels around the edges of a frame (e.g., column 0, row 0)
    # Check corners and borders of first frame to see their color distribution
    border_colors = []
    for x in range(fw):
        border_colors.append(img.getpixel((x, 0)))
        border_colors.append(img.getpixel((x, fh - 1)))
    for y in range(fh):
        border_colors.append(img.getpixel((0, y)))
        border_colors.append(img.getpixel((fw - 1, y)))
        
    # Count frequency of colors
    from collections import Counter
    c = Counter([p[:3] for p in border_colors])
    print("Most common border colors (R, G, B):")
    for col, count in c.most_common(10):
        print(f"Color: {col}, Count: {count}")
else:
    print("robotvang.png not found!")
