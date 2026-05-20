import pygame
import os

pygame.init()
surf = pygame.display.set_mode((100, 100))

base = os.path.dirname(os.path.abspath(__file__))
sprite_path = "c:/Users/LENOVO/OneDrive/Pictures/Desktop/KT1(game)/unnamed (2).jpg"

try:
    img = pygame.image.load(sprite_path).convert_alpha()
    w, h = img.get_width(), img.get_height()
    cols, rows = 8, 4
    fw, fh = w // cols, h // rows
    
    # Góc top-left làm màu nền
    bg_color = img.get_at((0, 0))
    print("Detected bg:", bg_color)
    
    # Cắt thử 1 frame
    col, row = 0, 1
    sub = img.subsurface(pygame.Rect(col * fw, row * fh, fw, fh)).copy()
    
    # Tạo surface trong suốt
    result = pygame.Surface((fw, fh), pygame.SRCALPHA)
    
    # Lọc màu xanh lá (38, 166, 91) hoặc bất kỳ màu xanh nào trong khoảng màu này
    for y in range(fh):
        for x in range(fw):
            color = sub.get_at((x, y))
            # Nếu pixel gần giống màu nền
            dist = ((color[0]-57)**2 + (color[1]-186)**2 + (color[2]-68)**2)**0.5
            if dist < 45:
                continue
            result.set_at((x, y), color)
            
    print("Successfully processed a green frame!")
except Exception as e:
    print("Error:", e)
