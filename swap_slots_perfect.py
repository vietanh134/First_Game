from PIL import Image

def swap_slots_perfect():
    # Mở ảnh gốc sạch của bạn
    img = Image.open('weapon_ui_backup.png')
    w, h = img.size
    
    # Coordinates phát hiện chính xác từ đường phân chia
    split_x = 246
    split_y = 114
    
    # Cắt chính xác ô trang bị hàng trên (Balo) từ X = 246 trở đi
    top_right = img.crop((split_x, 0, w, split_y))
    
    # Cắt chính xác ô trang bị hàng dưới (Mũ) từ X = 246 trở đi
    bottom_right = img.crop((split_x, split_y, w, h))
    
    # Tạo bản sao ảnh gốc
    new_img = img.copy()
    
    # Dán hoán đổi vị trí: Mũ lên hàng trên, Balo xuống hàng dưới
    new_img.paste(bottom_right, (split_x, 0))
    new_img.paste(top_right, (split_x, split_y))
    
    # Lưu đè vào weapon_ui.png
    new_img.save('weapon_ui.png')
    print("Successfully swapped slots pixel-perfectly with exact coordinates!")

if __name__ == '__main__':
    swap_slots_perfect()
