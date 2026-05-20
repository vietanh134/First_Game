"""Refine green chromakey removal for olive-green robot on neon-green background"""
from PIL import Image
import os, colorsys

img_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "unnamed (2).jpg")
img = Image.open(img_path).convert("RGBA")
w, h = img.size
cols, rows = 6, 4
fw, fh = w // cols, h // rows

out_dir = os.path.dirname(os.path.abspath(__file__))

# Sample background colors to understand the range
print("Background color samples (corners of frame [0,0]):")
for px, py in [(5,5), (5,10), (10,5), (160,5), (160,130), (5,130)]:
    r, g, b = img.getpixel((px, py))[:3]
    h_val, s_val, v_val = colorsys.rgb_to_hsv(r/255.0, g/255.0, b/255.0)
    print(f"  ({px},{py}): RGB=({r},{g},{b}), HSV=({h_val*360:.0f},{s_val*100:.0f}%,{v_val*100:.0f}%)")

# Sample robot body colors 
print("\nRobot body color samples (center of frame [1,0]):")
for px, py in [(70,30), (80,40), (85,50), (90,60), (75,70), (85,80)]:
    r, g, b = img.getpixel((px, py + fh))[:3]  # row 1
    h_val, s_val, v_val = colorsys.rgb_to_hsv(r/255.0, g/255.0, b/255.0)
    print(f"  ({px},{py}): RGB=({r},{g},{b}), HSV=({h_val*360:.0f},{s_val*100:.0f}%,{v_val*100:.0f}%)")

# Method v3: Pure green background is > (0, 160, 0) with high saturation
def is_green_bg_v3(r, g, b):
    """Background-only: high brightness green with high purity"""
    if g < 100:
        return False
    # The background is bright neon green (~0,180-220,0 range)
    # Robot armor is olive (80-140, 100-160, 60-120)
    # Key difference: background has very low R and B relative to G
    green_ratio = g / max(1, max(r, b))
    avg_rb = (r + b) / 2
    
    # Pure neon green: G is much higher than R and B, and G is bright
    if green_ratio > 1.6 and g > 140 and avg_rb < 130:
        return True
    # Also catch bright lime green
    if g > 170 and r < 150 and b < 100 and green_ratio > 1.3:
        return True
    return False

# Method v4: Use the specific background color range from samples
def is_green_bg_v4(r, g, b):
    """Target the specific neon green background"""
    h, s, v = colorsys.rgb_to_hsv(r/255.0, g/255.0, b/255.0)
    h_deg = h * 360
    # Background is in pure green hue (90-150 degrees), high saturation (>50%), high value
    if 70 < h_deg < 160 and s > 0.45 and v > 0.55:
        # But not the dark olive green of the robot
        # Robot armor: lower saturation, lower value
        if s > 0.55 and v > 0.65:
            return True
        # Very pure green (high sat) is definitely background
        if s > 0.70:
            return True
    return False

# Test v3 and v4
for method_name, method in [("v3", is_green_bg_v3), ("v4", is_green_bg_v4)]:
    preview = Image.new("RGBA", (fw * 6, fh * 4), (40, 40, 40, 255))
    for row in range(rows):
        for col in range(cols):
            x0, y0 = col * fw, row * fh
            frame = Image.new("RGBA", (fw, fh), (0, 0, 0, 0))
            for py in range(fh):
                for px in range(fw):
                    r, g, b = img.getpixel((x0 + px, y0 + py))[:3]
                    if not method(r, g, b):
                        frame.putpixel((px, py), (r, g, b, 255))
            preview.paste(frame, (col * fw, row * fh), frame)
    preview.save(os.path.join(out_dir, f"green_robot_{method_name}.png"))
    print(f"Saved green_robot_{method_name}.png")
