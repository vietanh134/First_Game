from PIL import Image
import os

img_path = "robotvang.png"
if os.path.exists(img_path):
    img = Image.open(img_path).convert("RGBA")
    w, h = img.size
    rows = 4
    fh = h // rows
    
    print(f"Analyzing {img_path} ({w}x{h}):")
    for r in range(rows):
        row_img = img.crop((0, r * fh, w, (r + 1) * fh))
        # Find horizontal columns of active pixels
        active_cols = []
        for x in range(w):
            has_pixel = False
            for y in range(fh):
                r2, g2, b2, a2 = row_img.getpixel((x, y))
                if a2 > 10 and not (r2 > 235 and g2 > 235 and b2 > 235):
                    has_pixel = True
                    break
            active_cols.append(has_pixel)
            
        # Group contiguous active/inactive segments
        segments = []
        in_segment = False
        start_x = 0
        for x in range(w):
            if active_cols[x] and not in_segment:
                in_segment = True
                start_x = x
            elif not active_cols[x] and in_segment:
                in_segment = False
                segments.append((start_x, x - 1))
        if in_segment:
            segments.append((start_x, w - 1))
            
        print(f"Row {r}: Found {len(segments)} sprites:")
        for idx, (s, e) in enumerate(segments):
            print(f"  Sprite {idx}: X={s} to {e} (width={e-s+1})")
else:
    print("robotvang.png not found!")
