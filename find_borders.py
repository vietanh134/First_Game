from PIL import Image

def find_borders():
    img = Image.open('weapon_ui_backup.png')
    w, h = img.size
    
    # Tìm dòng cột dọc có màu gần tối (đường viền dọc phân chia cột vũ khí và cột trang bị)
    # Chúng ta quét từ giữa màn hình (x = 180 đến 250) để tìm cột có lượng pixel tối lớn nhất
    best_x = w // 2
    min_bright = 999999
    
    for x in range(150, 250):
        # Tính độ sáng trung bình của cột x
        bright_sum = 0
        for y in range(h):
            r, g, b, *a = img.getpixel((x, y))
            bright_sum += (r + g + b)
        if bright_sum < min_bright:
            min_bright = bright_sum
            best_x = x
            
    # Tương tự tìm đường phân chia nằm ngang cho 2 ô trang bị bên phải (y = 80 đến 160)
    best_y = h // 2
    min_bright_y = 999999
    for y in range(80, 160):
        bright_sum = 0
        for x in range(best_x, w):
            r, g, b, *a = img.getpixel((x, y))
            bright_sum += (r + g + b)
        if bright_sum < min_bright_y:
            min_bright_y = bright_sum
            best_y = y
            
    print(f"Borders found at: Vertical Split X = {best_x}, Horizontal Split Y = {best_y}")

if __name__ == '__main__':
    find_borders()
