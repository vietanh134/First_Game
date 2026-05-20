import pygame
pygame.init()

# Tải ảnh gốc
img = pygame.image.load('btn_custom.png')

# Tọa độ vùng nút tối màu bên trong
x = 61
y = 374
w = 962 - 61 + 1
h = 644 - 374 + 1

# Tạo surface mới chứa vùng crop
cropped_surf = pygame.Surface((w, h), pygame.SRCALPHA)
cropped_surf.blit(img, (0, 0), (x, y, w, h))

# Lưu đè lại vào file btn_custom.png
pygame.image.save(cropped_surf, 'btn_custom.png')
print("Successfully cropped and saved btn_custom.png!")
