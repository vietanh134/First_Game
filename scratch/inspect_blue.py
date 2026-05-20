import os, pygame
pygame.init()
pygame.display.set_mode((100, 100))

# Tải ảnh
img = pygame.image.load("53400032-5b67-479a-9406-253fcffdb61f.jpg")
w, h = img.get_width(), img.get_height()
cols, rows = 8, 4
fw, fh = w // cols, h // rows

print(f"Blue sheet size: {w}x{h}, cell size: {fw}x{fh}")

# Cắt thử 1 frame từ mỗi vùng
# Vùng 1: Row 0, Col 0 (Down)
# Vùng 2: Row 0, Col 4 (Up ở hàng 0)
# Vùng 3: Row 1, Col 0 (Up ở hàng 1?)
# Vùng 4: Row 2, Col 0 (Right)
# Vùng 5: Row 3, Col 0 (Left)

os.makedirs("scratch/test_blue", exist_ok=True)
pygame.image.save(img.subsurface(pygame.Rect(0 * fw, 0 * fh, fw, fh)), "scratch/test_blue/r0_c0_down.png")
pygame.image.save(img.subsurface(pygame.Rect(4 * fw, 0 * fh, fw, fh)), "scratch/test_blue/r0_c4_up.png")
pygame.image.save(img.subsurface(pygame.Rect(0 * fw, 1 * fh, fw, fh)), "scratch/test_blue/r1_c0.png")
pygame.image.save(img.subsurface(pygame.Rect(0 * fw, 2 * fh, fw, fh)), "scratch/test_blue/r2_c0_right.png")
pygame.image.save(img.subsurface(pygame.Rect(0 * fw, 3 * fh, fw, fh)), "scratch/test_blue/r3_c0_left.png")

print("Blue inspect frames saved successfully!")
