from PIL import Image

def swap_slots():
    # Mở ảnh gốc
    img = Image.open('weapon_ui_backup.png')
    w, h = img.size
    
    # Chia đôi chiều rộng và chiều cao
    mid_x = w // 2 # ~201
    mid_y = h // 2 # ~119
    
    # Cắt ô trang bị bên phải hàng trên (Balo)
    top_right = img.crop((mid_x, 0, w, mid_y))
    
    # Cắt ô trang bị bên phải hàng dưới (Mũ)
    bottom_right = img.crop((mid_x, mid_y, w, h))
    
    # Tạo ảnh mới từ ảnh gốc
    new_img = img.copy()
    
    # Dán ngược lại: Hàng dưới (Mũ) lên hàng trên, hàng trên (Balo) xuống hàng dưới
    new_img.paste(bottom_right, (mid_x, 0))
    new_img.paste(top_right, (mid_x, mid_y))
    
    # Lưu đè vào weapon_ui.png
    new_img.save('weapon_ui.png')
    print("Successfully swapped Helmet (to top) and Backpack (to bottom) pixel-perfectly!")

if __name__ == '__main__':
    swap_slots()
