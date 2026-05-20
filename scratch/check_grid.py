import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pygame
pygame.init()
pygame.display.set_mode((100, 100))

# Tải ảnh quái xanh.png
img = pygame.image.load("quái xanh.png")
w, h = img.get_width(), img.get_height()
rows = 4
fh = h // rows # 135

print(f"Image Size: {w}x{h}")
print(f"Row height: {fh}")

for r in range(rows):
    # Xác định số cột cho từng hàng cụ thể
    if r in [0, 1]:
        cols = 6
    else:
        cols = 7
    
    fw = w // cols
    row_status = []
    
    # Đảm bảo thư mục test_frames tồn tại để lưu các ảnh cắt thử kiểm tra
    os.makedirs("scratch/test_frames", exist_ok=True)
    
    for c in range(cols):
        sub = img.subsurface(pygame.Rect(c * fw, r * fh, fw, fh)).copy()
        
        # Đếm pixel có content
        active_pixels = 0
        min_x, min_y = fw, fh
        max_x, max_y = 0, 0
        for y in range(fh):
            for x in range(fw):
                if sub.get_at((x, y))[3] > 10:
                    active_pixels += 1
                    min_x = min(min_x, x)
                    min_y = min(min_y, y)
                    max_x = max(max_x, x)
                    max_y = max(max_y, y)
        
        if active_pixels > 100:
            content_w = max_x - min_x + 1
            content_h = max_y - min_y + 1
            row_status.append(f"Col{c}:({content_w}x{content_h})")
            # Lưu thử để xem
            pygame.image.save(sub, f"scratch/test_frames/row_{r}_col_{c}.png")
        else:
            row_status.append(f"Col{c}:empty")
            
    print(f"Row {r} ({cols} cols, fw={fw}): {' | '.join(row_status)}")
