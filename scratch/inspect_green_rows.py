import os, pygame
pygame.init()
pygame.display.set_mode((100, 100))

img = pygame.image.load("quái xanh.png")
w, h = img.get_width(), img.get_height()
fh = h // 4

os.makedirs("scratch/test_green_rows", exist_ok=True)
# Cắt cột đầu tiên của mỗi hàng
pygame.image.save(img.subsurface(pygame.Rect(0, 0 * fh, 150, fh)), "scratch/test_green_rows/row0.png")
pygame.image.save(img.subsurface(pygame.Rect(0, 1 * fh, 150, fh)), "scratch/test_green_rows/row1.png")
pygame.image.save(img.subsurface(pygame.Rect(0, 2 * fh, 150, fh)), "scratch/test_green_rows/row2.png")
pygame.image.save(img.subsurface(pygame.Rect(0, 3 * fh, 150, fh)), "scratch/test_green_rows/row3.png")

print("Green rows first frames saved successfully!")
