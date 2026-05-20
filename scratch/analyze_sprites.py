from PIL import Image

img = Image.open("c:/Users/LENOVO/OneDrive/Pictures/Desktop/KT1(game)/unnamed (2).jpg")
w, h = img.size

# Lấy màu nền từ góc top-left (0,0)
bg_color = img.getpixel((0, 0))
print("Background Color:", bg_color)

# Tìm các khoảng không gian trống để phân chia hàng và cột
# Hãy tìm hàng
non_bg_rows = []
for y in range(h):
    has_non_bg = False
    for x in range(w):
        pix = img.getpixel((x, y))
        # So sánh màu với màu nền (cho phép sai số nhỏ)
        diff = sum(abs(pix[i] - bg_color[i]) for i in range(3))
        if diff > 30: # Có màu khác nền
            has_non_bg = True
            break
    non_bg_rows.append(has_non_bg)

# Tìm các hàng liên tục có chứa sprite
rows_ranges = []
in_row = False
start_y = 0
for y, has in enumerate(non_bg_rows):
    if has and not in_row:
        start_y = y
        in_row = True
    elif not has and in_row:
        rows_ranges.append((start_y, y))
        in_row = False
if in_row:
    rows_ranges.append((start_y, h))

print("Row ranges:")
for i, r in enumerate(rows_ranges):
    print(f"Row {i}: y from {r[0]} to {r[1]} (height: {r[1]-r[0]})")

# Với mỗi hàng, tìm các cột chứa sprite
for i, (ry_start, ry_end) in enumerate(rows_ranges):
    non_bg_cols = []
    for x in range(w):
        has_non_bg = False
        for y in range(ry_start, ry_end):
            pix = img.getpixel((x, y))
            diff = sum(abs(pix[j] - bg_color[j]) for j in range(3))
            if diff > 30:
                has_non_bg = True
                break
        non_bg_cols.append(has_non_bg)
        
    cols_ranges = []
    in_col = False
    start_x = 0
    for x, has in enumerate(non_bg_cols):
        if has and not in_col:
            start_x = x
            in_col = True
        elif not has and in_col:
            cols_ranges.append((start_x, x))
            in_col = False
    if in_col:
        cols_ranges.append((start_x, w))
        
    print(f"Row {i} columns:")
    for j, c in enumerate(cols_ranges):
         print(f"  Col {j}: x from {c[0]} to {c[1]} (width: {c[1]-c[0]})")
