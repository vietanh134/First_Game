import pygame, math, os
from constants import *

# Tải ảnh nền màn hình chờ (image.png)
BG_IMAGE = None
try:
    bg_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'image.png')
    if os.path.exists(bg_path):
        BG_IMAGE = pygame.image.load(bg_path)
        BG_IMAGE = pygame.transform.scale(BG_IMAGE, (WIDTH, HEIGHT))
except Exception as e:
    print("Không tải được ảnh nền image.png:", e)

# Tải ảnh avatar từ thư mục (avatar_1.png, avatar_2.png, avatar_3.png)
AVATAR_IMAGES = {}
try:
    for i in (1, 2, 3):
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"avatar_{i}.png")
        if os.path.exists(path):
            img = pygame.image.load(path)
            # Scale về kích thước avatar tròn có đường kính 60px (bán kính 30px)
            AVATAR_IMAGES[i] = pygame.transform.scale(img, (60, 60))
        else:
            AVATAR_IMAGES[i] = None
except Exception as e:
    print("Lỗi tải hình ảnh avatar:", e)

# Tải ảnh hiển thị vũ khí ở màn hình chờ (weapon_ui.png)
WEAPON_UI_IMG = None
try:
    weapon_ui_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'weapon_ui.png')
    if not os.path.exists(weapon_ui_path):
        weapon_ui_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'weapon_ui_backup.png')
    if os.path.exists(weapon_ui_path):
        WEAPON_UI_IMG = pygame.image.load(weapon_ui_path)
except Exception as e:
    print("Lỗi tải weapon_ui.png hoặc weapon_ui_backup.png:", e)

# Tải các ảnh nút menu
BTN_IMAGES = []
try:
    btn_configs = [
        ('btn_play.png', 250, 50),
        ('btn_custom.png', 250, 50),
        ('btn_equip.png', 250, 50),
        ('btn_settings.png', 250, 50),
        ('btn_exit.png', 250, 50)
    ]
    for filename, target_w, target_h in btn_configs:
        img_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
        if os.path.exists(img_path):
            img = pygame.image.load(img_path)
            img_scaled = pygame.transform.scale(img, (target_w, target_h))
            BTN_IMAGES.append(img_scaled)
        else:
            BTN_IMAGES.append(None)
except Exception as e:
    print("Lỗi tải ảnh nút menu:", e)

def get_menu_button_rects():
    """Trả về danh sách các Rect của các nút trên menu chính để xử lý click chuột"""
    rects = []
    w, h = 250, 50
    start_y = 260
    gap = 15
    for i in range(5):
        rects.append(pygame.Rect(WIDTH // 2 - w // 2 - 70, start_y + i * (h + gap), w, h))
    return rects

# Font hỗ trợ tiếng Việt tốt trên Windows
VN_FONT = "segoeui"

# Cache font để tránh tạo lại mỗi frame
_font_cache = {}

def _get_font(size, font_name=None, bold=False):
    """Lấy font từ cache, tạo mới nếu chưa có, hỗ trợ load ttf cục bộ"""
    key = (font_name or VN_FONT, size, bold)
    if key not in _font_cache:
        import os
        if font_name and font_name.endswith('.ttf'):
            font_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), font_name)
            if os.path.exists(font_path):
                _font_cache[key] = pygame.font.Font(font_path, size)
            else:
                _font_cache[key] = pygame.font.SysFont(VN_FONT, size, bold=bold)
        else:
            _font_cache[key] = pygame.font.SysFont(font_name or VN_FONT, size, bold=bold)
    return _font_cache[key]

def draw_text(surf, text, x, y, size=24, color=WHITE, center=False, font_name=None, bold=False):
    font = _get_font(size, font_name, bold)
    txt = font.render(text, True, color)
    if center:
        surf.blit(txt, (x - txt.get_width() // 2, y - txt.get_height() // 2))
    else:
        surf.blit(txt, (x, y))
    return txt.get_rect(topleft=(x - (txt.get_width()//2 if center else 0), y - (txt.get_height()//2 if center else 0)))

def draw_text_alpha(surf, text, x, y, size=24, color=WHITE, center=False, alpha=255):
    """Vẽ text với alpha (độ trong suốt)"""
    font = _get_font(size)
    txt = font.render(text, True, color)
    txt_surf = pygame.Surface(txt.get_size(), pygame.SRCALPHA)
    txt_surf.blit(txt, (0, 0))
    txt_surf.set_alpha(alpha)
    if center:
        surf.blit(txt_surf, (x - txt.get_width() // 2, y - txt.get_height() // 2))
    else:
        surf.blit(txt_surf, (x, y))

def draw_story(surf, elapsed_ms=0):
    """Vẽ màn hình câu chuyện với hiệu ứng typewriter chuyên nghiệp và điện ảnh"""
    if BG_IMAGE:
        surf.blit(BG_IMAGE, (0, 0))
        # Lớp phủ tối mờ để làm nổi bật văn bản
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 190)) # Tối hơn 1 chút (190) để chữ nổi bật hơn
        surf.blit(overlay, (0, 0))
    else:
        surf.fill((10, 10, 20))

    # 1. Hiệu ứng nền - Bụi sáng/Tàn tro bay lơ lửng trong gió cực kỳ điện ảnh (40 hạt)
    t = pygame.time.get_ticks()
    for i in range(40):
        speed_y = 0.04 + (i % 3) * 0.03
        px = (i * 47 + int(math.sin(t / 800 + i) * 20)) % WIDTH
        py = (HEIGHT - int(t * speed_y + i * 30)) % HEIGHT
        
        size = 1 + (i % 2)
        glow = int(80 + 70 * math.sin(t / 400 + i * 1.5))
        p_color = (glow, int(glow * 0.75), int(glow * 0.4)) # Hạt tàn lửa màu vàng cam ấm áp
        
        pygame.draw.circle(surf, p_color, (px, py), size)
        if size > 1:
            glow_surf = pygame.Surface((size*4, size*4), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (*p_color, 35), (size*2, size*2), size*2)
            surf.blit(glow_surf, (px - size*2, py - size*2))

    # 2. Hiệu ứng Scanline (CRT) cổ điển chuyên nghiệp
    for y in range(0, HEIGHT, 4):
        scanline = pygame.Surface((WIDTH, 1), pygame.SRCALPHA)
        scanline.fill((0, 0, 0, 12))
        surf.blit(scanline, (0, y))

    # 3. Khung bốn góc màn hình phong cách Sci-Fi Terminal hiện đại
    pad = 30
    len_f = 25
    f_color = (0, 200, 255, 90)
    f_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    pygame.draw.lines(f_surf, f_color, False, [(pad, pad + len_f), (pad, pad), (pad + len_f, pad)], 2)
    pygame.draw.lines(f_surf, f_color, False, [(WIDTH - pad, pad + len_f), (WIDTH - pad, pad), (WIDTH - pad - len_f, pad)], 2)
    pygame.draw.lines(f_surf, f_color, False, [(pad, HEIGHT - pad - len_f), (pad, HEIGHT - pad), (pad + len_f, HEIGHT - pad)], 2)
    pygame.draw.lines(f_surf, f_color, False, [(WIDTH - pad, HEIGHT - pad - len_f), (WIDTH - pad, HEIGHT - pad), (WIDTH - pad - len_f, HEIGHT - pad)], 2)
    surf.blit(f_surf, (0, 0))

    # 4. Hiệu ứng Vignette (tối mờ 4 góc) làm nổi bật phần trung tâm
    vignette = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    for r in range(0, 120, 15):
        alpha = int((r / 120) ** 2 * 120)
        pygame.draw.rect(vignette, (0, 0, 0, alpha), (r, r, WIDTH - 2*r, HEIGHT - 2*r), 15)
    surf.blit(vignette, (0, 0))

    lines = [
        "NGỌN ĐÈN CUỐI CÙNG",
        "",
        "Năm 2050, thế giới sụp đổ hoàn toàn.",
        "Đại dịch robot nổi loạn tàn phá nhân loại,",
        "khiến mọi thành phố chìm vào bóng đêm.",
        "",
        "Bạn là người sống sót duy nhất,",
        "trong tay chỉ có một cây gậy bóng đèn,",
        "và một khẩu súng năng lượng thô sơ.",
        "",
        "Xung quanh là bóng tối vô chậm,",
        "nơi lũ robot khát máu đang săn lùng...",
        "",
        "Nhiệm vụ của bạn:",
        "Tiêu diệt toàn bộ robot ở mỗi khu vực",
        "để kích hoạt Cổng Năng Lượng qua màn.",
        "",
        "Vượt qua 6 màn chơi đầy thử thách,",
        "mang lại ánh sáng hòa bình cho thế giới!",
        "",
        "Hãy thắp sáng hy vọng cuối cùng!"
    ]

    CHAR_SPEED = 30     # Tăng tốc gõ chữ nhẹ (30ms) để người đọc không bị sốt ruột
    LINE_PAUSE = 200    # Dừng giữa các dòng ngắn hơn 1 chút cho mượt mà
    FADE_DURATION = 150

    cumulative_time = 0
    all_done = True

    for i, line in enumerate(lines):
        line_start_time = cumulative_time

        if not line:  # Dòng trống
            cumulative_time += LINE_PAUSE
            continue

        # Chưa đến dòng này
        if elapsed_ms < line_start_time:
            all_done = False
            break

        # Tính số ký tự hiển thị
        time_in_line = elapsed_ms - line_start_time
        chars_to_show = min(len(line), int(time_in_line / CHAR_SPEED) + 1)

        if chars_to_show < len(line):
            all_done = False

        visible_text = line[:chars_to_show]

        # Màu sắc, kích thước và font chữ
        if i == 0:
            c = (255, 215, 0)
            sz = 46
            fn = "vt323.ttf"
            cy = 75
        else:
            c = (210, 215, 230)
            sz = 20
            fn = None
            cy = 135 + i * 26

        # Vẽ bóng đổ mờ tạo chiều sâu chuyên nghiệp
        draw_text(surf, visible_text, WIDTH // 2 + 1, cy + 1, sz, (15, 10, 5), True, fn)
        # Vẽ văn bản chính
        draw_text(surf, visible_text, WIDTH // 2, cy, sz, c, True, fn)

        # Cập nhật thời gian tích lũy
        cumulative_time = line_start_time + len(line) * CHAR_SPEED + LINE_PAUSE

    # Con trỏ nhấp nháy ở cuối dòng đang gõ
    if not all_done:
        cursor_blink = (t // 300) % 2
        if cursor_blink:
            # Tìm dòng đang gõ
            cum = 0
            for i, line in enumerate(lines):
                if not line:
                    cum += LINE_PAUSE
                    continue
                if elapsed_ms < cum:
                    break
                time_in = elapsed_ms - cum
                chars = min(len(line), int(time_in / CHAR_SPEED) + 1)
                if chars < len(line):
                    # Vẽ cursor nhấp nháy màu cyan neon hiện đại
                    cy = 75 if i == 0 else 135 + i * 26
                    font = _get_font(sz, fn)
                    partial = font.render(line[:chars], True, WHITE)
                    cx = WIDTH // 2 + partial.get_width() // 2 + 4
                    pygame.draw.rect(surf, (0, 255, 255), (cx, cy - sz // 2 + 2, 2, sz - 2))
                    break

    # 5. Hướng dẫn bỏ qua cốt truyện nhấp nháy tinh tế ở dưới cùng màn hình
    skip_t = "Nhấn ENTER để vào sảnh chờ  |  Press ENTER to skip story"
    pulse_color = int(120 + 80 * math.sin(t / 250))
    
    if all_done:
        blink = (t // 500) % 2
        if blink:
            draw_text(surf, "Nhấn phím bất kỳ để tiếp tục...", WIDTH // 2, HEIGHT - 55, 20, (150, 255, 150), True)
    else:
        draw_text(surf, skip_t, WIDTH // 2, HEIGHT - 35, 15, (pulse_color, pulse_color, pulse_color + 20), True)

    return all_done

_combined_ui_cache = None
_combined_ui_cached_keys = None
_cached_split_x = None
_cached_split_y = None

def get_combined_weapon_ui(unlocked_weapons):
    global _combined_ui_cache, _combined_ui_cached_keys, _cached_split_x, _cached_split_y
    
    # Tạo key duy nhất để kiểm tra thay đổi
    current_key = ",".join(sorted(unlocked_weapons))
    
    if _combined_ui_cache is not None and _combined_ui_cached_keys == current_key:
        return _combined_ui_cache
        
    backup_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'weapon_ui_backup.png')
    if not os.path.exists(backup_path):
        return None
        
    try:
        base_img = pygame.image.load(backup_path).convert_alpha()
        w, h = base_img.get_size()
        
        # Độ lớn súng: pistol < smg < shotgun < sniper < advanced_sniper
        gun_sizes = {
            'pistol': 1,
            'smg': 2,
            'shotgun': 3,
            'sniper': 4,
            'advanced_sniper': 5
        }
        
        valid_guns = [g for g in unlocked_weapons if g in gun_sizes]
        valid_guns.sort(key=lambda g: gun_sizes[g])
        
        # Tự động tìm đường chia dựa trên ảnh thực tế (hoàn toàn tương thích mọi độ phân giải)
        if _cached_split_x is None:
            # 1. Tìm vertical split_x (quét vùng từ 70% đến 85% chiều rộng)
            start_x = int(w * 0.70)
            end_x = int(w * 0.85)
            split_x = int(w * 0.78)
            min_bright_x = 999999999
            
            for x in range(start_x, end_x):
                bright_sum = 0
                for y in range(0, h, 2):  # Bước nhảy 2 để chạy nhanh hơn
                    r, g, b, *a = base_img.get_at((x, y))
                    bright_sum += (r + g + b)
                if bright_sum < min_bright_x:
                    min_bright_x = bright_sum
                    split_x = x
                    
            # 2. Tìm horizontal split_y (quét vùng từ 40% đến 60% chiều cao)
            start_y = int(h * 0.40)
            end_y = int(h * 0.60)
            split_y = int(h * 0.50)
            min_bright_y = 999999999
            
            for y in range(start_y, end_y):
                bright_sum = 0
                for x in range(split_x, w, 2):  # Chỉ quét vùng bên phải của split_x
                    r, g, b, *a = base_img.get_at((x, y))
                    bright_sum += (r + g + b)
                if bright_sum < min_bright_y:
                    min_bright_y = bright_sum
                    split_y = y
            _cached_split_x = split_x
            _cached_split_y = split_y
        else:
            split_x = _cached_split_x
            split_y = _cached_split_y
                
        # Thêm lề đệm (padding) tỷ lệ theo kích thước ảnh thực tế
        pad_x = int(split_x * 0.05)
        pad_y = int(split_y * 0.08)
        
        # Ô trống 1 (Trên - Súng nhỏ hơn): Y từ 0 -> split_y
        if len(valid_guns) >= 1:
            _draw_gun_in_slot(base_img, valid_guns[0], pad_x, pad_y, split_x - 2 * pad_x, split_y - 2 * pad_y)
            
        # Ô trống 2 (Dưới - Súng lớn hơn): Y từ split_y -> h
        if len(valid_guns) >= 2:
            _draw_gun_in_slot(base_img, valid_guns[1], pad_x, split_y + pad_y, split_x - 2 * pad_x, h - split_y - 2 * pad_y)
            
        # Đồng thời lưu đè vào file weapon_ui.png để đồng bộ ra máy tính
        ui_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'weapon_ui.png')
        pygame.image.save(base_img, ui_path)
        
        _combined_ui_cache = base_img
        _combined_ui_cached_keys = current_key
        
        return base_img
    except Exception as e:
        print("Lỗi tạo ảnh kết hợp súng:", e)
        return None

def _draw_gun_in_slot(surf, gun_id, rx, ry, rw, rh):
    img_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"{gun_id}.png")
    if os.path.exists(img_path):
        try:
            g_img = pygame.image.load(img_path).convert_alpha()
            
            # Tự động loại bỏ các khoảng trống trong suốt xung quanh khẩu súng
            bbox = g_img.get_bounding_rect()
            if bbox.width > 0 and bbox.height > 0:
                g_img = g_img.subsurface(bbox)
            
            gw, gh = g_img.get_size()
            
            # Giới hạn kích thước súng tối đa chiếm khoảng 90% chiều rộng và 80% chiều cao của ô trống để vừa khít đẹp mắt
            max_w = int(rw * 0.90)
            max_h = int(rh * 0.80)
            
            scale = min(max_w / gw, max_h / gh)
            new_w = int(gw * scale)
            new_h = int(gh * scale)
            
            scaled_gun = pygame.transform.scale(g_img, (new_w, new_h))
            
            # Căn giữa súng vào ô trống rx, ry, rw, rh
            tx = rx + (rw - new_w) // 2
            ty = ry + (rh - new_h) // 2
            
            surf.blit(scaled_gun, (tx, ty))
        except Exception:
            pass

def draw_menu(surf, selected, player_skin='mu', unlocked_weapons=['pistol']):
    if BG_IMAGE:
        surf.blit(BG_IMAGE, (0, 0))
    else:
        surf.fill((15, 15, 30))

    # === PANEL CHỌN SKIN (AVATAR CR7 TỰ DO) ===
    skins_info = [
        ('mu', 'MU', (200, 30, 30), (255, 255, 255)),
        ('rm', 'Real', (240, 240, 240), (30, 30, 30)),
        ('an', 'Nassr', (255, 215, 0), (30, 30, 255))
    ]
    
    for idx, (skin_id, name, j_color, n_color) in enumerate(skins_info):
        cx = 60 + idx * 72
        cy = 65
        r_av = 30
        
        is_active = (player_skin == skin_id)
        
        # Glow ring if active
        if is_active:
            glow_surf = pygame.Surface((r_av * 2 + 20, r_av * 2 + 20), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (255, 215, 0, 110), (r_av + 10, r_av + 10), r_av + 8)
            surf.blit(glow_surf, (cx - r_av - 10, cy - r_av - 10))
            pygame.draw.circle(surf, YELLOW, (cx, cy), r_av + 3, 3)
        else:
            pygame.draw.circle(surf, (80, 80, 80), (cx, cy), r_av + 2, 2)
            
        # Draw avatar image if available, otherwise draw the custom vector stickman
        avatar_img = AVATAR_IMAGES.get(idx + 1)
        if avatar_img:
            # Vẽ hình ảnh avatar tròn bằng cách blit hình ảnh đã scale (60x60)
            surf.blit(avatar_img, (cx - r_av, cy - r_av))
        else:
            # Draw jersey circle inside
            pygame.draw.circle(surf, j_color, (cx, cy), r_av)
            # Draw CR7 face and hair inside
            pygame.draw.circle(surf, (230, 180, 140), (cx, cy - 10), 8) # face
            pygame.draw.arc(surf, (40, 30, 20), (cx - 6, cy - 16, 12, 10), 0, math.pi, 3) # hair
            # Draw Number 7
            f_num = _get_font(18)
            t_num = f_num.render("7", True, n_color)
            surf.blit(t_num, (cx - t_num.get_width() // 2, cy - 4))
        
        # Checkmark if active
        if is_active:
            pygame.draw.circle(surf, (50, 220, 80), (cx + r_av - 5, cy - r_av + 5), 8)
            pygame.draw.circle(surf, WHITE, (cx + r_av - 5, cy - r_av + 5), 2.5)

    # Vẽ weapon_ui.png động ở giữa bên phải
    combined_ui = get_combined_weapon_ui(unlocked_weapons)
    if not combined_ui:
        combined_ui = WEAPON_UI_IMG
        
    if combined_ui:
        target_w = 380  # Tăng kích thước hình to ra (từ 250 lên 380)
        target_h = int(combined_ui.get_height() * (target_w / combined_ui.get_width()))
        wx = WIDTH - target_w - 120  # Dịch sang trái (tăng khoảng cách lề phải từ 20 lên 120)
        wy = HEIGHT // 2 - target_h // 2 + 70  # Cho xuống dưới 1 xíu (cộng thêm 70px)
        
        # Hiệu ứng nổi lên nhẹ khi Hover chuột (Lifting/Float animation)
        mx, my = pygame.mouse.get_pos()
        panel_rect = pygame.Rect(wx, wy, target_w, target_h)
        is_hover = panel_rect.collidepoint(mx, my)
        
        if is_hover:
            # Nhấc lên cao 12px và giãn nở to hơn 5%
            wx -= 10
            wy -= 12
            target_w += 20
            target_h = int(combined_ui.get_height() * (target_w / combined_ui.get_width()))
            
        scaled_img = pygame.transform.scale(combined_ui, (target_w, target_h))
        
        if is_hover:
            # Tạo bóng phát sáng neon màu cam mờ phía sau cực chất
            glow_surf = pygame.Surface((target_w + 30, target_h + 30), pygame.SRCALPHA)
            pygame.draw.rect(glow_surf, (255, 120, 0, 40), (15, 15, target_w, target_h), border_radius=15)
            surf.blit(glow_surf, (wx - 15, wy - 15))
            
            # Vẽ hộp Balo/Súng bay lên kèm viền vàng sáng rực
            surf.blit(scaled_img, (wx, wy))
            pygame.draw.rect(surf, (255, 180, 0), (wx, wy, target_w, target_h), 2, border_radius=8)
            
            # Nhãn chỉ dẫn lơ lửng màu vàng lấp lánh phía trên
            draw_text(surf, "🎒 CLICK ĐỂ MỞ HÀNH TRANG", wx + target_w // 2, wy - 22, 14, (255, 215, 0), True, None, False)
        else:
            surf.blit(scaled_img, (wx, wy))

    # Title "NGỌN ĐÈN CUỐI CÙNG" phong cách Retro Arcade Pixel cực đỉnh
    menu_center_x = WIDTH // 2
    title_text = "NGỌN ĐÈN CUỐI CÙNG"
    title_y = 80
    font_file = "vt323.ttf"
    
    # 1. Hào quang phát sáng (Glow) đỏ cam huyền ảo ở sau
    for r in range(6, 0, -2):
        f_glow = _get_font(62, font_file)
        t_glow = f_glow.render(title_text, True, (255, 80, 0))
        t_glow_surf = pygame.Surface(t_glow.get_size(), pygame.SRCALPHA)
        t_glow_surf.blit(t_glow, (0, 0))
        t_glow_surf.set_alpha(int(50 - r * 5))
        for dx in [-r, 0, r]:
            for dy in [-r, 0, r]:
                surf.blit(t_glow_surf, (menu_center_x - t_glow.get_width() // 2 + dx, title_y - t_glow.get_height() // 2 + dy))

    # 2. Lớp bóng đổ 3D đen sâu phía dưới tạo độ nổi khối kiểu Retro
    for i in range(4, 0, -1):
        draw_text(surf, title_text, menu_center_x + i, title_y + i, 62, (15, 10, 5), True, font_file)

    # 3. Lớp chữ chính màu Vàng Chanh neon rực rỡ
    draw_text(surf, title_text, menu_center_x, title_y, 62, (255, 225, 0), True, font_file)

    
    rects = get_menu_button_rects()
    for i, rect in enumerate(rects):
        is_sel = (i == selected)
        img = BTN_IMAGES[i] if i < len(BTN_IMAGES) else None

        if img:
            if is_sel:
                # Sáng nguyên bản (100% alpha)
                img.set_alpha(255)
                # Phóng to nhẹ nút khi được chọn (1.08x)
                w, h = img.get_size()
                sw = int(w * 1.08)
                sh = int(h * 1.08)
                img_scaled = pygame.transform.scale(img, (sw, sh))
                # Căn giữa tại tọa độ nút cũ
                sx = rect.centerx - sw // 2
                sy = rect.centery - sh // 2
                
                # Vẽ viền neon sáng lấp lánh rực rỡ đằng sau nút được chọn
                glow = pygame.Surface((sw + 12, sh + 12), pygame.SRCALPHA)
                pygame.draw.rect(glow, (255, 160, 50, 75), (0, 0, sw + 12, sh + 12), border_radius=10)
                surf.blit(glow, (sx - 6, sy - 6))
                
                surf.blit(img_scaled, (sx, sy))
                
                if i == 1:
                    pass
                
                # Vẽ mũi tên chỉ hướng bên trái và phải (kèm bóng đổ đen)
                draw_text(surf, "▶", sx - 25 + 1, rect.centery + 1, 22, (0, 0, 0), True)
                draw_text(surf, "▶", sx - 25, rect.centery, 22, YELLOW, True)
                draw_text(surf, "◀", sx + sw + 25 + 1, rect.centery + 1, 22, (0, 0, 0), True)
                draw_text(surf, "◀", sx + sw + 25, rect.centery, 22, YELLOW, True)
            else:
                # Nút không được chọn sẽ mờ đi và tối hơn (tầm 110/255 alpha) để nổi bật nút chọn
                img.set_alpha(110)
                surf.blit(img, (rect.x, rect.y))
        else:
            # Fallback nếu không load được ảnh
            c = YELLOW if is_sel else (160, 160, 180)
            sz = 30 if is_sel else 24
            if is_sel:
                pygame.draw.rect(surf, (40, 40, 70), (rect.x - 10, rect.y, rect.w + 20, rect.h), border_radius=8)
                pygame.draw.rect(surf, YELLOW, (rect.x - 10, rect.y, rect.w + 20, rect.h), 2, border_radius=8)
            
            # Đặt tên nhãn nút
            btn_labels = ["VÀO CHƠI", "GIỚI THIỆU", "VẬT PHẨM", "CÀI ĐẶT", "THOÁT GAME"]
            label = btn_labels[i] if i < len(btn_labels) else f"NÚT {i}"
            draw_text(surf, label, rect.centerx, rect.centery, sz, c, True)
def draw_level_select(surf, selected, levels_unlocked):
    """Vẽ màn hình chọn màn với hệ thống khóa/mở khóa"""
    surf.fill((12, 12, 28))

    # Hiệu ứng nền - particle sáng mờ
    t = pygame.time.get_ticks()
    for i in range(30):
        px = (i * 149 + int(t * 0.02 * (i % 3 + 1))) % WIDTH
        py = (i * 97 + int(t * 0.015 * (i % 2 + 1))) % HEIGHT
        brightness = int(30 + 20 * math.sin(t / 700 + i))
        pygame.draw.circle(surf, (brightness, brightness, brightness + 15), (px, py), 1)

    # Tiêu đề
    draw_text(surf, "CHỌN MÀN", WIDTH // 2, 40, 42, YELLOW, True)
    draw_text(surf, "Phá đảo từng màn để mở khóa màn tiếp theo", WIDTH // 2, 85, 18, (140, 140, 170), True)

    # Grid 3x2 cho 6 màn
    card_w, card_h = 340, 200
    gap_x, gap_y = 40, 30
    start_x = (WIDTH - (card_w * 3 + gap_x * 2)) // 2
    start_y = 120

    # Màu nền cho từng level card
    level_card_colors = [
        (55, 55, 70),     # Thành phố
        (25, 50, 35),     # Rừng
        (100, 90, 55),    # Sa mạc
        (55, 55, 60),     # Nghĩa địa
        (70, 90, 110),    # Hầm băng
        (35, 65, 35),     # Old Trafford
    ]

    for i in range(6):
        col = i % 3
        row = i // 3
        cx = start_x + col * (card_w + gap_x)
        cy = start_y + row * (card_h + gap_y)

        is_sel = (i == selected)
        is_unlocked = (i < levels_unlocked)

        # Card nền
        card_rect = pygame.Rect(cx, cy, card_w, card_h)
        card_surf = pygame.Surface((card_w, card_h), pygame.SRCALPHA)

        if is_unlocked:
            # Màn đã mở khóa
            bg_col = level_card_colors[i]
            card_surf.fill((*bg_col, 220))

            # Viền sáng gradient khi selected
            if is_sel:
                glow_alpha = int(160 + 60 * math.sin(t / 250))
                pygame.draw.rect(card_surf, (*YELLOW, glow_alpha), (0, 0, card_w, card_h), 3, border_radius=12)
                # Glow effect bên ngoài
                glow_surf = pygame.Surface((card_w + 12, card_h + 12), pygame.SRCALPHA)
                pygame.draw.rect(glow_surf, (255, 220, 50, 30), (0, 0, card_w + 12, card_h + 12), border_radius=14)
                surf.blit(glow_surf, (cx - 6, cy - 6))
            else:
                pygame.draw.rect(card_surf, (100, 100, 120, 200), (0, 0, card_w, card_h), 2, border_radius=12)
        else:
            # Màn bị khóa - tối hơn nhiều
            card_surf.fill((30, 30, 40, 240))
            if is_sel:
                pygame.draw.rect(card_surf, (100, 60, 60, 200), (0, 0, card_w, card_h), 3, border_radius=12)
            else:
                pygame.draw.rect(card_surf, (60, 60, 70, 200), (0, 0, card_w, card_h), 2, border_radius=12)

        surf.blit(card_surf, (cx, cy))

        # Nội dung card
        if is_unlocked:
            # Số màn (góc trên trái)
            num_bg = pygame.Surface((40, 28), pygame.SRCALPHA)
            num_bg.fill((0, 0, 0, 120))
            surf.blit(num_bg, (cx + 10, cy + 10))
            draw_text(surf, f"{i + 1}", cx + 30, cy + 24, 22, YELLOW, True)

            # Tên màn
            draw_text(surf, LEVEL_NAMES[i], cx + card_w // 2, cy + 60, 24, WHITE, True)

            # Thông tin robot
            counts = LEVEL_ROBOTS[i]
            total_robots = sum(counts.values()) if isinstance(counts, dict) else sum(counts)
            draw_text(surf, f"Robot: {total_robots}", cx + card_w // 2, cy + 95, 18, (200, 150, 150), True)

            # Chi tiết loại robot
            robot_types = []
            # Map type ID to (Name, Color)
            type_info = {
                'blue': ('Xanh', (50, 120, 255)),
                'white': ('Trắng', (230, 230, 230)),
                'green': ('Xanh lá', (50, 220, 80)),
                'yellow': ('Vàng', (255, 220, 50)),
                'boss': ('Boss', (255, 200, 50)),
                'white_giant': ('Khổng lồ', (240, 240, 240)),
            }
            if isinstance(counts, dict):
                for rtype, count in counts.items():
                    if count > 0:
                        name, color = type_info.get(rtype, (rtype, (200, 200, 200)))
                        robot_types.append((name, count, color))
            else:
                # Fallback old format
                type_names = ['Xanh', 'Trắng', 'Xanh lá', 'Boss']
                type_colors = [(50, 120, 255), (230, 230, 230), (50, 220, 80), (255, 200, 50)]
                for j, count in enumerate(counts):
                    if count > 0:
                        robot_types.append((type_names[j], count, type_colors[j]))

            rx = cx + 20
            for name, count, color in robot_types:
                # Chấm tròn màu
                pygame.draw.circle(surf, color, (rx + 6, cy + 130), 5)
                draw_text(surf, f"{count}", rx + 16, cy + 122, 14, (200, 200, 220))
                rx += 50

            # Biểu tượng sân/theme nhỏ ở góc dưới
            theme_icons = ['🏙', '🌲', '🏜', '⚰', '❄', '⚽']
            draw_text(surf, f"Màn {i+1}", cx + card_w // 2, cy + 165, 16, (120, 120, 150), True)

            # Viền đã mở khóa - icon ổ khóa mở
            pygame.draw.circle(surf, (50, 200, 80), (cx + card_w - 25, cy + 20), 10)
            # Dấu check
            check_pts = [
                (cx + card_w - 30, cy + 20),
                (cx + card_w - 26, cy + 25),
                (cx + card_w - 19, cy + 14)
            ]
            pygame.draw.lines(surf, WHITE, False, check_pts, 2)

        else:
            # Màn bị khóa
            # Số màn (mờ)
            draw_text(surf, f"MÀN {i + 1}", cx + card_w // 2, cy + 50, 22, (80, 80, 100), True)

            # Biểu tượng ổ khóa lớn ở giữa
            lock_cx = cx + card_w // 2
            lock_cy = cy + card_h // 2 + 5

            # Thân ổ khóa
            lock_body_rect = pygame.Rect(lock_cx - 16, lock_cy - 5, 32, 26)
            pygame.draw.rect(surf, (100, 80, 60), lock_body_rect, border_radius=4)
            pygame.draw.rect(surf, (140, 110, 70), lock_body_rect, 2, border_radius=4)

            # Vòng cung ổ khóa phía trên
            arc_rect = pygame.Rect(lock_cx - 10, lock_cy - 22, 20, 22)
            pygame.draw.arc(surf, (140, 110, 70), arc_rect, 0, math.pi, 3)

            # Lỗ khóa
            pygame.draw.circle(surf, (50, 40, 30), (lock_cx, lock_cy + 5), 4)
            pygame.draw.rect(surf, (50, 40, 30), (lock_cx - 1, lock_cy + 7, 3, 6))

            # Text khóa
            draw_text(surf, "ĐÃ KHÓA", cx + card_w // 2, cy + card_h - 35, 16, (120, 70, 70), True)

            # Tên màn mờ nhạt
            draw_text(surf, LEVEL_NAMES[i], cx + card_w // 2, cy + card_h - 18, 14, (60, 60, 80), True)

            # Hiệu ứng xích chéo mờ
            chain_color = (60, 60, 70, 80)
            for offset in range(-1, 2):
                pygame.draw.line(surf, (50, 50, 60),
                               (cx + 10 + offset * 30, cy + card_h - 5),
                               (cx + card_w - 10 + offset * 30, cy + 5), 1)

    # Hướng dẫn
    draw_text(surf, "↑↓ ←→ Chọn màn   |   ENTER Bắt đầu   |   ESC Quay lại", WIDTH // 2, HEIGHT - 40, 18, (130, 130, 160), True)

    # Hiệu ứng nhấp nháy cho text hướng dẫn nếu màn bị khóa
    if selected >= levels_unlocked:
        blink = (t // 400) % 2
        if blink:
            draw_text(surf, "⚠ Hãy phá đảo các màn trước để mở khóa!", WIDTH // 2, HEIGHT - 70, 18, (255, 120, 80), True)

def draw_controls_screen(surf):
    surf.fill((15, 15, 30))
    draw_text(surf, "ĐIỀU KHIỂN", WIDTH // 2, 40, 36, YELLOW, True)
    controls = [
        ("WASD", "Di chuyển nhân vật"),
        ("SPACE", "Bật/tắt đèn hình tam giác (miễn phí)"),
        ("J / Chuột Trái", "Tấn công (Kiếm chém / Súng bắn)"),
        ("L", "Đổi vũ khí (Kiếm ↔ Súng)"),
        ("1, 2, G / Cuộn Chuột", "Đổi qua lại các súng đã mua (khi cầm súng)"),
        ("R", "Nạp đạn (Khi cầm súng và hết đạn)"),
        ("T", "Cắm đèn trụ (-20 NL, sáng 10s)"),
        ("Q", "Nhấp nháy đèn choáng robot xanh lá (-15 NL)"),
        ("E", "Quét đèn hiện robot 250px (-10 NL)"),
        ("F", "Xung sáng toàn bộ, mù robot 3s (-40 NL)"),
        ("Shift", "Chạy nhanh +50%"),
        ("ESC", "Quay lại menu"),
    ]
    for i, (key, desc) in enumerate(controls):
        y = 95 + i * 36
        draw_text(surf, key, 200, y, 18, (100, 200, 255))
        draw_text(surf, desc, 440, y, 18, (200, 200, 220))
    draw_text(surf, "Nhấn ESC để quay lại", WIDTH // 2, HEIGHT - 35, 18, (150, 150, 180), True)

def draw_vector_weapon(surf, wid, cx, cy):
    """Vẽ phác thảo blueprint vector phát sáng neon siêu đẹp cho từng khẩu súng"""
    # Tạo một surface bán trong suốt có kích thước 400x200
    w_surf = pygame.Surface((400, 200), pygame.SRCALPHA)
    
    # Vẽ ô lưới tọa độ mờ kiểu bản vẽ thiết kế (Blueprint) cực kỳ đẹp và chuyên nghiệp!
    for x in range(0, 400, 20):
        pygame.draw.line(w_surf, (0, 150, 255, 20), (x, 0), (x, 200))
    for y in range(0, 200, 20):
        pygame.draw.line(w_surf, (0, 150, 255, 20), (0, y), (400, y))
        
    # Lấy thông số màu chủ đạo của súng từ constants
    color = GUNS_DATA[wid]['color']
    line_color = (*color, 255)
    
    # Phác thảo các bộ phận súng bằng các đường vẽ phẳng tinh tế
    if wid == 'pistol':
        # Báng súng (Grip)
        pygame.draw.polygon(w_surf, (80, 80, 95, 200), [(160, 120), (145, 175), (170, 175), (185, 120)])
        pygame.draw.polygon(w_surf, line_color, [(160, 120), (145, 175), (170, 175), (185, 120)], 2)
        # Thân súng (Receiver)
        pygame.draw.rect(w_surf, (60, 60, 75, 220), (150, 85, 110, 35), border_radius=3)
        pygame.draw.rect(w_surf, line_color, (150, 85, 110, 35), 2, border_radius=3)
        # Nòng súng (Barrel)
        pygame.draw.rect(w_surf, (100, 100, 120, 200), (260, 90, 60, 15))
        pygame.draw.rect(w_surf, line_color, (260, 90, 60, 15), 2)
        # Ống ngắm pin năng lượng (Battery Scope)
        pygame.draw.rect(w_surf, (color[0], color[1], color[2], 100), (170, 70, 70, 15), border_radius=2)
        pygame.draw.rect(w_surf, line_color, (170, 70, 70, 15), 1, border_radius=2)
        # Điểm tiếp năng lượng phát sáng
        pygame.draw.circle(w_surf, color, (205, 77), 4)
        
    elif wid == 'smg':
        # Báng xếp (Foldable stock)
        pygame.draw.line(w_surf, line_color, (120, 100), (70, 110), 3)
        pygame.draw.line(w_surf, line_color, (70, 110), (60, 150), 3)
        # Tay cầm (Grip)
        pygame.draw.polygon(w_surf, (50, 50, 60, 200), [(160, 120), (145, 165), (165, 165), (180, 120)])
        pygame.draw.polygon(w_surf, line_color, [(160, 120), (145, 165), (165, 165), (180, 120)], 2)
        # Thân súng SMG nhỏ gọn
        pygame.draw.rect(w_surf, (70, 70, 85, 220), (120, 85, 110, 35), border_radius=3)
        pygame.draw.rect(w_surf, line_color, (120, 85, 110, 35), 2, border_radius=3)
        # Nòng ngắn
        pygame.draw.rect(w_surf, (90, 90, 105, 200), (230, 92, 50, 12))
        pygame.draw.rect(w_surf, line_color, (230, 92, 50, 12), 2)
        # Băng đạn cong dài (Banana clip)
        pygame.draw.polygon(w_surf, (40, 40, 50, 220), [(145, 120), (125, 175), (145, 175), (165, 120)])
        pygame.draw.polygon(w_surf, line_color, [(145, 120), (125, 175), (145, 175), (165, 120)], 2)

    elif wid == 'shotgun':
        # Báng súng gỗ/sắt cổ điển
        pygame.draw.polygon(w_surf, (90, 70, 60, 220), [(100, 140), (70, 175), (120, 175), (140, 135)])
        pygame.draw.polygon(w_surf, line_color, [(100, 140), (70, 175), (120, 175), (140, 135)], 2)
        # Thân súng Shotgun lớn
        pygame.draw.rect(w_surf, (70, 75, 90, 220), (130, 95, 90, 45), border_radius=4)
        pygame.draw.rect(w_surf, line_color, (130, 95, 90, 45), 2, border_radius=4)
        # Nòng kép (Double Barrel)
        pygame.draw.rect(w_surf, (90, 95, 110, 200), (220, 98, 140, 16))
        pygame.draw.rect(w_surf, line_color, (220, 98, 140, 16), 2)
        pygame.draw.rect(w_surf, (90, 95, 110, 200), (220, 116, 140, 16))
        pygame.draw.rect(w_surf, line_color, (220, 116, 140, 16), 2)
        # Điểm sạc năng lượng màu đỏ cam
        pygame.draw.circle(w_surf, color, (175, 118), 7)
        
    elif wid == 'assault':
        # Báng súng áp vai (Stock)
        pygame.draw.polygon(w_surf, (50, 50, 60, 200), [(80, 95), (60, 145), (90, 145), (120, 100)])
        pygame.draw.polygon(w_surf, line_color, [(80, 95), (60, 145), (90, 145), (120, 100)], 2)
        # Tay cầm (Grip)
        pygame.draw.polygon(w_surf, (50, 50, 60, 200), [(160, 125), (145, 170), (165, 170), (180, 125)])
        pygame.draw.polygon(w_surf, line_color, [(160, 125), (145, 170), (165, 170), (180, 125)], 2)
        # Thân súng dài
        pygame.draw.rect(w_surf, (70, 70, 85, 220), (120, 90, 140, 40), border_radius=3)
        pygame.draw.rect(w_surf, line_color, (120, 90, 140, 40), 2, border_radius=3)
        # Nòng dài có khe tản nhiệt
        pygame.draw.rect(w_surf, (90, 90, 105, 200), (260, 98, 90, 18))
        pygame.draw.rect(w_surf, line_color, (260, 98, 90, 18), 2)
        for i in range(4):
            pygame.draw.line(w_surf, line_color, (270 + i*20, 103), (270 + i*20, 111), 2)
        # Hộp đạn lớn (Magazine drum) tròn phát sáng màu xanh lá
        pygame.draw.circle(w_surf, (40, 60, 40, 220), (195, 155), 24)
        pygame.draw.circle(w_surf, line_color, (195, 155), 24, 2)
        pygame.draw.circle(w_surf, color, (195, 155), 14, 3)
        
    elif wid == 'sniper':
        # Báng súng bắn tỉa nặng
        pygame.draw.polygon(w_surf, (40, 45, 60, 220), [(70, 95), (45, 160), (95, 160), (120, 105)])
        pygame.draw.polygon(w_surf, line_color, [(70, 95), (45, 160), (95, 160), (120, 105)], 2)
        # Thân súng khổng lồ chứa lõi gia tốc hạt
        pygame.draw.rect(w_surf, (60, 65, 80, 220), (120, 90, 160, 48), border_radius=4)
        pygame.draw.rect(w_surf, line_color, (120, 90, 160, 48), 2, border_radius=4)
        # Nòng súng trường gia tốc hạt siêu dài
        pygame.draw.rect(w_surf, (80, 85, 100, 200), (280, 100, 110, 15))
        pygame.draw.rect(w_surf, line_color, (280, 100, 110, 15), 2)
        # Giảm thanh/Đầu nòng vuông lớn
        pygame.draw.rect(w_surf, (50, 50, 60, 220), (390, 95, 20, 25))
        pygame.draw.rect(w_surf, line_color, (390, 95, 20, 25), 2)
        # Ống ngắm Sniper năng lượng tầm xa khổng lồ (Amber Scope)
        pygame.draw.rect(w_surf, (40, 40, 50, 200), (150, 65, 85, 25), border_radius=2)
        pygame.draw.rect(w_surf, line_color, (150, 65, 85, 25), 2, border_radius=2)
        pygame.draw.line(w_surf, line_color, (192, 60), (192, 65), 2)
        pygame.draw.circle(w_surf, color, (155, 77), 5)
        pygame.draw.circle(w_surf, color, (230, 77), 5)
        # Chân đỡ súng (Bipod) gấp gọn phía dưới
        pygame.draw.line(w_surf, line_color, (290, 115), (275, 165), 2)
        pygame.draw.line(w_surf, line_color, (300, 115), (285, 165), 2)

    elif wid == 'advanced_sniper':
        # Báng súng bắn tỉa nâng cấp (Advanced stock)
        pygame.draw.polygon(w_surf, (40, 45, 60, 220), [(60, 90), (35, 165), (90, 165), (115, 100)])
        pygame.draw.polygon(w_surf, line_color, [(60, 90), (35, 165), (90, 165), (115, 100)], 2)
        # Thân súng gia tốc hạt tối tân
        pygame.draw.rect(w_surf, (60, 65, 80, 220), (115, 85, 170, 52), border_radius=4)
        pygame.draw.rect(w_surf, line_color, (115, 85, 170, 52), 2, border_radius=4)
        # Nòng gia tốc điện từ siêu dài (Railgun barrel)
        pygame.draw.rect(w_surf, (80, 85, 100, 200), (285, 95, 120, 18))
        pygame.draw.rect(w_surf, line_color, (285, 95, 120, 18), 2)
        # Bộ giảm thanh / Phanh đầu nòng cỡ lớn
        pygame.draw.rect(w_surf, (50, 50, 60, 220), (405, 90, 22, 28))
        pygame.draw.rect(w_surf, line_color, (405, 90, 22, 28), 2)
        # Ống ngắm chiến thuật siêu lớn phát sáng xanh lục (Advanced scope)
        pygame.draw.rect(w_surf, (40, 40, 50, 200), (145, 55, 95, 28), border_radius=3)
        pygame.draw.rect(w_surf, line_color, (145, 55, 95, 28), 2, border_radius=3)
        pygame.draw.circle(w_surf, (0, 255, 100), (150, 69), 6)
        pygame.draw.circle(w_surf, (0, 255, 100), (235, 69), 6)
        # Chân đỡ súng gấp góc (Bipod)
        pygame.draw.line(w_surf, line_color, (310, 113), (295, 170), 2)
        pygame.draw.line(w_surf, line_color, (320, 113), (305, 170), 2)
        
    surf.blit(w_surf, (cx - 200, cy - 100))

def draw_vector_pet(surf, pid, cx, cy):
    """Vẽ phác thảo vector phát sáng neon siêu ngộ nghĩnh cho từng loại pet"""
    p_surf = pygame.Surface((400, 200), pygame.SRCALPHA)
    
    # Ô lưới tọa độ mờ kiểu bản vẽ thiết kế (Blueprint)
    for x in range(0, 400, 20):
        pygame.draw.line(p_surf, (0, 255, 150, 15), (x, 0), (x, 200))
    for y in range(0, 200, 20):
        pygame.draw.line(p_surf, (0, 255, 150, 15), (0, y), (400, y))
        
    color = PETS_DATA[pid]['color']
    line_color = (*color, 255)
    
    if pid == 'mini_robot':
        # Thân chính (Quả cầu)
        pygame.draw.circle(p_surf, (40, 50, 60, 200), (200, 100), 45)
        pygame.draw.circle(p_surf, line_color, (200, 100), 45, 3)
        # Kính bảo hộ phát sáng (Visor)
        pygame.draw.rect(p_surf, color, (170, 85, 60, 16), border_radius=8)
        pygame.draw.circle(p_surf, WHITE, (200, 93), 4)
        # Ăng ten nhỏ phía trên
        pygame.draw.line(p_surf, line_color, (200, 55), (200, 35), 2)
        pygame.draw.circle(p_surf, color, (200, 32), 6)
        # Cánh phản lực nhỏ ở hai bên
        pygame.draw.polygon(p_surf, line_color, [(150, 100), (130, 80), (135, 120)])
        pygame.draw.polygon(p_surf, line_color, [(250, 100), (270, 80), (265, 120)])
        # Lửa đẩy nhỏ ở đáy
        pygame.draw.polygon(p_surf, (255, 100, 50), [(190, 145), (200, 165), (210, 145)])

    elif pid == 'plasma_pup':
        # Đầu cún
        pygame.draw.circle(p_surf, (50, 45, 60, 200), (200, 80), 30)
        pygame.draw.circle(p_surf, line_color, (200, 80), 30, 2)
        # Tai dài cụp
        pygame.draw.ellipse(p_surf, (40, 40, 50, 200), (160, 60, 20, 45))
        pygame.draw.ellipse(p_surf, line_color, (160, 60, 20, 45), 2)
        pygame.draw.ellipse(p_surf, (40, 40, 50, 200), (220, 60, 20, 45))
        pygame.draw.ellipse(p_surf, line_color, (220, 60, 20, 45), 2)
        # Thân cún
        pygame.draw.rect(p_surf, (50, 45, 60, 200), (170, 110, 60, 40), border_radius=10)
        pygame.draw.rect(p_surf, line_color, (170, 110, 60, 40), 2, border_radius=10)
        # Chân
        pygame.draw.line(p_surf, line_color, (185, 150), (185, 175), 3)
        pygame.draw.line(p_surf, line_color, (215, 150), (215, 175), 3)
        # Vòng cổ phát sáng
        pygame.draw.line(p_surf, color, (185, 110), (215, 110), 4)

    elif pid == 'lucky_cat':
        # Thân hình vòm
        pygame.draw.ellipse(p_surf, (65, 55, 40, 200), (170, 80, 60, 75))
        pygame.draw.ellipse(p_surf, line_color, (170, 80, 60, 75), 2)
        # Đầu mèo
        pygame.draw.circle(p_surf, (65, 55, 40, 200), (200, 70), 28)
        pygame.draw.circle(p_surf, line_color, (200, 70), 28, 2)
        # Tai nhọn
        pygame.draw.polygon(p_surf, line_color, [(175, 55), (170, 30), (190, 48)])
        pygame.draw.polygon(p_surf, line_color, [(225, 55), (230, 30), (210, 48)])
        # Bàn chân vẫy tài lộc (vẫy lên)
        pygame.draw.ellipse(p_surf, color, (225, 60, 16, 32))
        pygame.draw.ellipse(p_surf, line_color, (225, 60, 16, 32), 2)
        # Đồng tiền vàng ở bụng
        pygame.draw.circle(p_surf, color, (200, 115), 14)
        pygame.draw.circle(p_surf, WHITE, (200, 115), 6)
        
    surf.blit(p_surf, (cx - 200, cy - 100))

def draw_grab_hero(surf, cx, cy, wid=None):
    """Vẽ nhân vật Grab Hero cực kỳ dễ thương mặc áo khoác xanh lá, đội mũ bảo hiểm"""
    # 1. Thân người (Áo khoác Grab màu xanh lá đậm)
    pygame.draw.rect(surf, (0, 150, 60), (cx - 15, cy, 30, 45), border_radius=4)
    # Sọc trắng/đen Grab đặc trưng chéo qua ngực
    pygame.draw.line(surf, WHITE, (cx - 12, cy + 10), (cx + 12, cy + 30), 3)
    
    # 2. Đầu & Mũ bảo hiểm Grab (màu xanh lá tươi có kính đen)
    # Mũ bảo hiểm
    pygame.draw.circle(surf, (0, 180, 80), (cx, cy - 18), 16)
    # Kính mũ bảo hiểm (Visor màu xám đen)
    pygame.draw.ellipse(surf, (40, 40, 40), (cx - 10, cy - 23, 20, 10))
    # Quai mũ
    pygame.draw.line(surf, (20, 20, 20), (cx - 12, cy - 10), (cx + 12, cy - 10), 2)
    
    # 3. Quần (Màu xám/đen)
    pygame.draw.rect(surf, (30, 30, 35), (cx - 14, cy + 45, 11, 28), border_radius=2)
    pygame.draw.rect(surf, (30, 30, 35), (cx + 3, cy + 45, 11, 28), border_radius=2)
    
    # 4. Giày (Màu xám trắng)
    pygame.draw.ellipse(surf, (150, 150, 160), (cx - 16, cy + 70, 14, 8))
    pygame.draw.ellipse(surf, (150, 150, 160), (cx + 2, cy + 70, 14, 8))
    
    # 5. Cánh tay nâng súng
    if wid:
        # Màu của súng
        gun_color = GUNS_DATA.get(wid, {}).get('color', YELLOW)
        # Tay cầm súng
        pygame.draw.line(surf, (0, 150, 60), (cx - 10, cy + 20), (cx + 20, cy + 15), 5)
        # Súng
        # Vẽ một phiên bản súng pixel nhỏ ở tay nhân vật
        pygame.draw.rect(surf, gun_color, (cx + 12, cy + 6, 26, 12), border_radius=2)
        pygame.draw.rect(surf, (40, 40, 45), (cx + 18, cy + 16, 5, 8)) # Tay cầm súng
        pygame.draw.line(surf, gun_color, (cx + 38, cy + 9), (cx + 46, cy + 9), 3) # Nòng súng

_shop_image_cache = {}

def draw_shop_screen(surf, selected_weapon, unlocked_weapons, coins, preview_weapon, error_timer=0,
                     unlocked_pets=None, selected_pet=None, shop_tab='gun', preview_pet='mini_robot', player_skin='mu'):
    """Vẽ sảnh Cửa hàng súng & Pet (Shop Grab Hero) chuyên nghiệp theo phong cách chính thức"""
    if unlocked_pets is None: unlocked_pets = []
    surf.fill((12, 8, 5))  # Nền tối đất bụi bặm kiểu game sinh tồn PUBG/FreeFire

    # Vẽ ô lưới nhẹ màu cam rỉ sét/đất đỏ ở background
    t = pygame.time.get_ticks()
    for x in range(0, WIDTH, 40):
        pygame.draw.line(surf, (60, 25, 10, 40), (x, 0), (x, HEIGHT))
    for y in range(0, HEIGHT, 40):
        pygame.draw.line(surf, (60, 25, 10, 40), (0, y), (WIDTH, y))

    # Lớp phủ vignette tối góc phát sáng màu cam hổ phách
    glow_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    pygame.draw.rect(glow_surf, (255, 95, 0, 12), (0, 0, WIDTH, HEIGHT))
    surf.blit(glow_surf, (0, 0))
    
    # Vệt sáng radar quét quét dọc màn hình cửa hàng (Scanline)
    scan_y = (t // 6) % HEIGHT
    scanline = pygame.Surface((WIDTH, 3), pygame.SRCALPHA)
    scanline.fill((255, 95, 0, 25))  # Vệt quét màu cam dạ quang bán trong suốt mảnh
    surf.blit(scanline, (0, scan_y))

    # --- KHUNG HUD CHỮ U CAM HỔ PHÁCH (AMBER HUD BORDER) ---
    # Vẽ đường viền lớn bao quanh toàn bộ nội dung cửa hàng kiểu quân đội cứng cáp
    pygame.draw.rect(surf, (255, 95, 0), (30, 95, 1140, 525), 2, border_radius=6)

    # --- TIÊU ĐỀ CHÍNH ---
    draw_text(surf, "KHO VU KHI SINH TON", WIDTH // 2, 25, 32, (255, 120, 0), True, "press_start_2p.ttf")
    # Biển hiển thị Vàng tích lũy
    draw_text(surf, f"Vàng tích lũy: {coins}", WIDTH // 2, 65, 20, YELLOW, True)

    # --- NÚT ĐÓNG (X) GÓC TRÊN BÊN PHẢI ---
    # Thiết kế nút đóng phong cách quân đội cực ngầu
    close_rect = pygame.Rect(1110, 35, 40, 40)
    pygame.draw.rect(surf, (60, 20, 15), close_rect, border_radius=6)
    pygame.draw.rect(surf, (255, 95, 0), close_rect, 1, border_radius=6)
    draw_text(surf, "X", 1130, 55, 18, (255, 95, 0), True, "press_start_2p.ttf")

    # --- HỆ THỐNG TABS Ở TRÊN CÙNG (Y: 105 - 155) ---
    # Chỉ giữ lại 2 Tab: MUA SÚNG và MUA PET, cùng 2 nút mũi tên để luân phiên chuyển đổi
    
    # 1. Nút mũi tên Trái (<)
    left_arrow_rect = pygame.Rect(260, 105, 40, 50)
    pygame.draw.rect(surf, (25, 20, 15), left_arrow_rect, border_radius=4)
    pygame.draw.rect(surf, (255, 120, 0), left_arrow_rect, 1, border_radius=4)
    # Vẽ mũi tên hướng sang trái kiểu Vector neon
    pygame.draw.polygon(surf, (255, 120, 0), [(285, 120), (271, 130), (285, 140)], 3)

    # 2. Vẽ tab 1: MUA SÚNG
    bg_color2 = (220, 50, 30) if shop_tab == 'gun' else (25, 20, 15)
    text_color2 = WHITE if shop_tab == 'gun' else (150, 140, 130)
    pygame.draw.rect(surf, bg_color2, (320, 105, 270, 50), border_radius=4)
    pygame.draw.rect(surf, (255, 120, 0) if shop_tab == 'gun' else (50, 45, 40), (320, 105, 270, 50), 1, border_radius=4)
    draw_text(surf, "MUA SÚNG", 455, 120, 18, text_color2, True)

    # 3. Vẽ tab 2: MUA PET
    bg_color3 = (220, 50, 30) if shop_tab == 'pet' else (25, 20, 15)
    text_color3 = WHITE if shop_tab == 'pet' else (150, 140, 130)
    pygame.draw.rect(surf, bg_color3, (610, 105, 270, 50), border_radius=4)
    pygame.draw.rect(surf, (255, 120, 0) if shop_tab == 'pet' else (50, 45, 40), (610, 105, 270, 50), 1, border_radius=4)
    draw_text(surf, "MUA PET", 745, 120, 18, text_color3, True)

    # 4. Nút mũi tên Phải (>)
    right_arrow_rect = pygame.Rect(900, 105, 40, 50)
    pygame.draw.rect(surf, (25, 20, 15), right_arrow_rect, border_radius=4)
    pygame.draw.rect(surf, (255, 120, 0), right_arrow_rect, 1, border_radius=4)
    # Vẽ mũi tên hướng sang phải kiểu Vector neon
    pygame.draw.polygon(surf, (255, 120, 0), [(915, 120), (929, 130), (915, 140)], 3)

    # --- PHẦN NỘI DUNG CHÍNH (Y: 175 - 610) ---
    
    # 1. CỘT TRÁI: DANH SÁCH LỰA CHỌN (X: 50 -> 550)
    pygame.draw.rect(surf, (18, 12, 10), (50, 170, 500, 435), border_radius=6)
    pygame.draw.rect(surf, (120, 45, 15), (50, 170, 500, 435), 1, border_radius=6)
    
    if shop_tab == 'gun':
        draw_text(surf, "Mua súng đẹp ngay tại sảnh (không cần chờ shop ingame)", 300, 180, 13, (150, 180, 160), True)
        
        weapons_list = ['pistol', 'shotgun', 'smg', 'sniper', 'advanced_sniper']
        for idx, wid in enumerate(weapons_list):
            info = GUNS_DATA[wid]
            card_y = 205 + idx * 76
            card_rect = pygame.Rect(60, card_y, 480, 68)
            
            is_previewed = (preview_weapon == wid)
            is_unlocked = (wid in unlocked_weapons)
            is_selected = (selected_weapon == wid)
            
            # Màu viền & nền thẻ dựa trên trạng thái
            if is_previewed:
                bg_color = (40, 25, 15, 240)
                border_color = YELLOW  # Viền vàng phát sáng khi chọn xem giống screenshot!
                border_width = 2
            else:
                bg_color = (18, 14, 12, 190)
                border_color = (80, 50, 40)
                border_width = 1
                
            card_bg = pygame.Surface((480, 68), pygame.SRCALPHA)
            card_bg.fill(bg_color)
            surf.blit(card_bg, (60, card_y))
            pygame.draw.rect(surf, border_color, card_rect, border_width, border_radius=6)
            
            # Hộp màu biểu tượng súng bên trái
            pygame.draw.rect(surf, info['color'], (75, card_y + 17, 34, 34), border_radius=4)
            pygame.draw.rect(surf, WHITE, (75, card_y + 17, 34, 34), 1, border_radius=4)
            
            # Tên súng & Specs phụ
            draw_text(surf, info['name'], 125, card_y + 13, 18, WHITE, False, "vt323.ttf")
            specs_text = f"DMG {info['damage']}  ROF {int(1.0/info['fire_rate'])}  MAG {info['clip_size']}"
            draw_text(surf, specs_text, 125, card_y + 40, 11, (130, 140, 135))
            
            # Giá hoặc "ĐÃ SỞ HỮU"
            if is_selected:
                draw_text(surf, "ĐANG DÙNG", 410, card_y + 24, 14, (255, 150, 0))
            elif is_unlocked:
                draw_text(surf, "ĐÃ SỞ HỮU", 410, card_y + 24, 14, (255, 127, 80)) # Màu đỏ/cam neon của ĐÃ SỞ HỮU
            else:
                draw_text(surf, f"{info['price']}$", 430, card_y + 24, 16, YELLOW)
                
    elif shop_tab == 'pet':
        draw_text(surf, "Mua pet đồng hành hỗ trợ chiến đấu cực mạnh", 300, 180, 13, (150, 180, 160), True)
        
        pets_list = ['mini_robot', 'plasma_pup', 'lucky_cat']
        for idx, pid in enumerate(pets_list):
            info = PETS_DATA[pid]
            card_y = 205 + idx * 130
            card_rect = pygame.Rect(60, card_y, 480, 115)
            
            is_previewed = (preview_pet == pid)
            is_unlocked = (pid in unlocked_pets)
            is_selected = (selected_pet == pid)
            
            if is_previewed:
                bg_color = (45, 25, 15, 240)
                border_color = YELLOW
                border_width = 2
            else:
                bg_color = (18, 14, 12, 190)
                border_color = (80, 50, 40)
                border_width = 1
                
            card_bg = pygame.Surface((480, 115), pygame.SRCALPHA)
            card_bg.fill(bg_color)
            surf.blit(card_bg, (60, card_y))
            pygame.draw.rect(surf, border_color, card_rect, border_width, border_radius=8)
            
            # Hộp màu biểu tượng Pet
            pygame.draw.rect(surf, info['color'], (80, card_y + 20, 75, 75), border_radius=6)
            pygame.draw.rect(surf, WHITE, (80, card_y + 20, 75, 75), 1, border_radius=6)
            
            # Tên Pet & Mô tả
            draw_text(surf, info['name'], 175, card_y + 15, 22, info['color'], False, "vt323.ttf")
            desc_lines = [info['desc'][i:i+32] for i in range(0, len(info['desc']), 32)]
            for d_idx, line in enumerate(desc_lines):
                draw_text(surf, line, 175, card_y + 45 + d_idx * 18, 12, (170, 160, 180))
            
            # Giá hoặc Trang bị
            if is_selected:
                draw_text(surf, "ĐỒNG HÀNH", 390, card_y + 15, 13, (255, 150, 0))
            elif is_unlocked:
                draw_text(surf, "ĐÃ SỞ HỮU", 390, card_y + 15, 13, (150, 150, 150))
            else:
                draw_text(surf, f"{info['price']}$", 410, card_y + 15, 16, YELLOW)

    # 2. CỘT PHẢI: CHI TIẾT XEM TRƯỚC (X: 570 -> 1120)
    pygame.draw.rect(surf, (15, 12, 10), (570, 170, 550, 435), border_radius=6)
    pygame.draw.rect(surf, (120, 45, 15), (570, 170, 550, 435), 1, border_radius=6)
    
    # ----------------- TACTICAL RADAR RETICLE (Survial Style) -----------------
    radar_surf = pygame.Surface((550, 435), pygame.SRCALPHA)
    rcx, rcy = 845 - 570, 310 - 170  # Tọa độ tương đối trong khung preview
    
    # 1. Vẽ các vòng tròn đồng tâm mờ neon cam
    pygame.draw.circle(radar_surf, (255, 95, 0, 20), (rcx, rcy), 130, 1)
    pygame.draw.circle(radar_surf, (255, 95, 0, 10), (rcx, rcy), 90, 1)
    pygame.draw.circle(radar_surf, (255, 95, 0, 30), (rcx, rcy), 50, 1)
    
    # 2. Vẽ hồng tâm chữ thập gián đoạn (classic shooter crosshair)
    pygame.draw.line(radar_surf, (255, 95, 0, 25), (rcx - 160, rcy), (rcx - 40, rcy), 1)
    pygame.draw.line(radar_surf, (255, 95, 0, 25), (rcx + 40, rcy), (rcx + 160, rcy), 1)
    pygame.draw.line(radar_surf, (255, 95, 0, 25), (rcx, rcy - 120), (rcx, rcy - 40), 1)
    pygame.draw.line(radar_surf, (255, 95, 0, 25), (rcx, rcy + 40), (rcx, rcy + 120), 1)
    
    # 3. Vẽ góc nhọn ngắm bắn (Corner bracket góc lục giác) xung quanh trung tâm
    bracket_size = 20
    b_dist = 105
    # Góc trên bên trái
    pygame.draw.line(radar_surf, (255, 120, 0, 40), (rcx - b_dist, rcy - b_dist), (rcx - b_dist + bracket_size, rcy - b_dist), 2)
    pygame.draw.line(radar_surf, (255, 120, 0, 40), (rcx - b_dist, rcy - b_dist), (rcx - b_dist, rcy - b_dist + bracket_size), 2)
    # Góc trên bên phải
    pygame.draw.line(radar_surf, (255, 120, 0, 40), (rcx + b_dist, rcy - b_dist), (rcx + b_dist - bracket_size, rcy - b_dist), 2)
    pygame.draw.line(radar_surf, (255, 120, 0, 40), (rcx + b_dist, rcy - b_dist), (rcx + b_dist, rcy - b_dist + bracket_size), 2)
    # Góc dưới bên trái
    pygame.draw.line(radar_surf, (255, 120, 0, 40), (rcx - b_dist, rcy + b_dist), (rcx - b_dist + bracket_size, rcy + b_dist), 2)
    pygame.draw.line(radar_surf, (255, 120, 0, 40), (rcx - b_dist, rcy + b_dist), (rcx - b_dist, rcy + b_dist - bracket_size), 2)
    # Góc dưới bên phải
    pygame.draw.line(radar_surf, (255, 120, 0, 40), (rcx + b_dist, rcy + b_dist), (rcx + b_dist - bracket_size, rcy + b_dist), 2)
    pygame.draw.line(radar_surf, (255, 120, 0, 40), (rcx + b_dist, rcy + b_dist), (rcx + b_dist, rcy + b_dist - bracket_size), 2)
    
    # 4. Vẽ telemetry dữ liệu la bàn quân đội
    t = pygame.time.get_ticks()
    font_radar = pygame.font.SysFont('Consolas', 11)
    radar_txt = font_radar.render("SYS: SAFE_ZONE_ARMORY [V2.5]", True, (255, 100, 0))
    radar_txt.set_alpha(100 + int(math.sin(t * 0.005) * 50))
    radar_surf.blit(radar_txt, (20, 20))
    
    telemetry_txt = font_radar.render("LAT: 10.7626 N | LNG: 106.6602 E | ALT: 24M", True, (255, 100, 0))
    telemetry_txt.set_alpha(70 + int(math.sin(t * 0.003) * 30))
    radar_surf.blit(telemetry_txt, (20, 395))
    
    surf.blit(radar_surf, (570, 170))
    # --------------------------------------------------------------------------
    
    if shop_tab == 'gun':
        p_info = GUNS_DATA[preview_weapon]
        draw_text(surf, p_info['name'], 845, 185, 26, YELLOW, True, "vt323.ttf")
        
        cache_key = ('gun', preview_weapon)
        if cache_key not in _shop_image_cache:
            gun_img_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"{preview_weapon}.png")
            g_img = None
            if os.path.exists(gun_img_path):
                try:
                    g_img = pygame.image.load(gun_img_path).convert_alpha()
                    g_img = pygame.transform.scale(g_img, (320, 120))
                except Exception:
                    pass
            _shop_image_cache[cache_key] = g_img
            
        g_img = _shop_image_cache[cache_key]
        if g_img:
            surf.blit(g_img, (685, 250))
        else:
            draw_vector_weapon(surf, preview_weapon, 845, 315)
            
        # [ĐÃ ẨN NHÂN VẬT THEO YÊU CẦU] Không còn vẽ nhân vật ở đây nữa để tập trung vào súng cực kỳ ngầu!
        
        draw_text(surf, f"Damage: {p_info['damage']}", 845, 470, 15, WHITE, True)
        draw_text(surf, f"Fire Rate: {int(1.0/p_info['fire_rate'])} RPS", 845, 492, 15, WHITE, True)
        draw_text(surf, f"Magazine: {p_info['clip_size']}", 845, 514, 15, WHITE, True)
        
        # Nút Hành động khổng lồ (MUA / TRANG BỊ)
        btn_rect = pygame.Rect(650, 545, 400, 48)
        is_unlocked = (preview_weapon in unlocked_weapons)
        is_selected = (selected_weapon == preview_weapon)
        
        if is_selected:
            pygame.draw.rect(surf, (100, 30, 20), btn_rect, border_radius=6)
            pygame.draw.rect(surf, (255, 120, 0), btn_rect, 1, border_radius=6)
            draw_text(surf, "✔ ĐANG SỬ DỤNG", 850, 560, 18, (255, 150, 0), True)
        elif is_unlocked:
            pygame.draw.rect(surf, (50, 55, 60), btn_rect, border_radius=6)
            pygame.draw.rect(surf, (255, 120, 0), btn_rect, 1, border_radius=6)
            draw_text(surf, "TRANG BỊ SÚNG NÀY", 850, 560, 18, WHITE, True)
        else:
            cost = p_info['price']
            can_afford = (coins >= cost)
            btn_color = (160, 50, 20) if can_afford else (90, 30, 30)
            border_color = (255, 120, 0) if can_afford else RED
            
            pygame.draw.rect(surf, btn_color, btn_rect, border_radius=6)
            pygame.draw.rect(surf, border_color, btn_rect, 1, border_radius=6)
            draw_text(surf, f"MUA NGAY - {cost}$", 850, 560, 18, WHITE, True)
            
    elif shop_tab == 'pet':
        p_info = PETS_DATA[preview_pet]
        draw_text(surf, p_info['name'], 845, 185, 26, YELLOW, True, "vt323.ttf")
        
        cache_key = ('pet', preview_pet)
        if cache_key not in _shop_image_cache:
            pet_img_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"{preview_pet}.png")
            p_img = None
            if os.path.exists(pet_img_path):
                try:
                    p_img = pygame.image.load(pet_img_path).convert_alpha()
                    p_img = pygame.transform.scale(p_img, (150, 150))
                except Exception:
                    pass
            _shop_image_cache[cache_key] = p_img
            
        p_img = _shop_image_cache[cache_key]
        if p_img:
            surf.blit(p_img, (770, 240))
        else:
            draw_vector_pet(surf, preview_pet, 845, 315)
            
        # [ĐÃ ẨN NHÂN VẬT THEO YÊU CẦU] Không còn vẽ nhân vật ở đây nữa để tập trung xem Pet cực ngầu!
        pygame.draw.circle(surf, p_info['color'], (845, 315), 18, 1)
        pygame.draw.circle(surf, WHITE, (845, 315), 4)
        
        draw_text(surf, "Tính Năng Hỗ Trợ Chiến Đấu:", 845, 470, 15, YELLOW, True)
        draw_text(surf, p_info['desc'], 845, 495, 14, WHITE, True)
        
        # Nút Hành động khổng lồ (MUA / TRANG BỊ)
        btn_rect = pygame.Rect(650, 545, 400, 48)
        is_unlocked = (preview_pet in unlocked_pets)
        is_selected = (selected_pet == preview_pet)
        
        if is_selected:
            pygame.draw.rect(surf, (100, 30, 20), btn_rect, border_radius=6)
            pygame.draw.rect(surf, (255, 120, 0), btn_rect, 1, border_radius=6)
            draw_text(surf, "✔ ĐANG ĐỒNG HÀNH", 850, 560, 18, (255, 150, 0), True)
        elif is_unlocked:
            pygame.draw.rect(surf, (50, 55, 60), btn_rect, border_radius=6)
            pygame.draw.rect(surf, (255, 120, 0), btn_rect, 1, border_radius=6)
            draw_text(surf, "MANG THEO PET", 850, 560, 18, WHITE, True)
        else:
            cost = p_info['price']
            can_afford = (coins >= cost)
            btn_color = (160, 50, 20) if can_afford else (90, 30, 30)
            border_color = (255, 120, 0) if can_afford else RED
            
            pygame.draw.rect(surf, btn_color, btn_rect, border_radius=6)
            pygame.draw.rect(surf, border_color, btn_rect, 1, border_radius=6)
            draw_text(surf, f"MỞ KHÓA PET - {cost}$", 850, 560, 18, WHITE, True)

    # --- NÚT TAB: +9999 VÀNG (góc trên bên trái, nổi bật) ---
    tab_rect = pygame.Rect(35, 35, 200, 40)
    tab_pulse = 180 + int(math.sin(t * 0.006) * 75)
    tab_bg = (40, 35, 10)
    tab_border = (255, 215, 0)
    pygame.draw.rect(surf, tab_bg, tab_rect, border_radius=8)
    pygame.draw.rect(surf, tab_border, tab_rect, 2, border_radius=8)
    # Hiệu ứng phát sáng vàng nhấp nháy
    glow_tab = pygame.Surface((208, 48), pygame.SRCALPHA)
    pygame.draw.rect(glow_tab, (255, 215, 0, max(0, min(255, tab_pulse - 180))), (0, 0, 208, 48), border_radius=10)
    surf.blit(glow_tab, (31, 31))
    draw_text(surf, "TAB  +9999 VÀNG", 135, 46, 15, (255, 230, 80), True)

    # Hiển thị súng/pet đã sở hữu
    if shop_tab == 'gun':
        gun_count = len(unlocked_weapons)
        draw_text(surf, f"Súng sở hữu: {gun_count}/5", 135, 82, 13, (150, 200, 150), True)
    elif shop_tab == 'pet':
        pet_count = len(unlocked_pets)
        draw_text(surf, f"Pet sở hữu: {pet_count}/3", 135, 82, 13, (150, 200, 150), True)

    # Hiển thị thông báo nhấp nháy báo lỗi
    if error_timer > 0:
        blink = (t // 150) % 2
        if blink:
            draw_text(surf, "KHÔNG ĐỦ VÀNG ĐỂ MUA!", 850, 515, 15, RED, True)

    # Phím thoát ở dưới cùng
    draw_text(surf, "Nhấn ESC hoặc ấn CHƠI/QUAY LẠI để quay về sảnh chính", WIDTH // 2, HEIGHT - 35, 15, (120, 140, 130), True)


_backpack_image_cache = {}
_backpack_overlay_surf = None

def draw_backpack_screen(surf, unlocked_weapons, equipped_weapons, unlocked_pets, selected_pet, coins, player_skin, mouse_pos, anim_t=1.0):
    global _backpack_overlay_surf
    if _backpack_overlay_surf is None:
        _backpack_overlay_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        _backpack_overlay_surf.fill((10, 10, 15, 210))
        
    # Tạo lớp phủ mờ dần (Fade-in)
    overlay_copy = _backpack_overlay_surf.copy()
    overlay_copy.set_alpha(int(255 * anim_t))
    surf.blit(overlay_copy, (0, 0))
    
    # 2. Khung viền kính mờ (Glassmorphism) ở giữa màn hình
    px = WIDTH // 2 - 450
    # Hiệu ứng trượt lên nhẹ (Slide up) từ py + 50 lên py trong 250ms
    py_target = HEIGHT // 2 - 280
    py = py_target + int(50 * (1.0 - anim_t))
    pw, ph = 900, 560
    
    # Vẽ bóng đổ và nền kính mờ
    pygame.draw.rect(surf, (20, 20, 28, 240), (px, py, pw, ph), border_radius=12)
    pygame.draw.rect(surf, (255, 120, 0), (px, py, pw, ph), 2, border_radius=12)
    
    # Tiêu đề cực ngầu
    draw_text(surf, "HÀNH TRANG TRANG BỊ CỦA CR7", WIDTH // 2, py + 25, 30, YELLOW, True, "vt323.ttf")
    # Đường kẻ phân tách tiêu đề phát sáng neon
    pygame.draw.line(surf, (255, 120, 0), (px + 50, py + 65), (px + pw - 50, py + 65), 2)
    
    # Hiển thị số tiền hiện có ở góc trên bên phải của bảng
    draw_text(surf, f"VÀNG: {coins}$", px + pw - 80, py + 30, 18, (100, 255, 120), True)
    
    # --- CỘT TRÁI: KHO VŨ KHÍ (Vũ khí đã mua & Trang bị) ---
    draw_text(surf, "⚔ KHO VŨ KHÍ (TRANG BỊ TỐI ĐA 2 SÚNG)", px + 50, py + 85, 16, YELLOW)
    # Lọc chỉ hiện súng đã mua/sở hữu
    weapons_list = [w for w in ['pistol', 'shotgun', 'smg', 'sniper', 'advanced_sniper'] if w in unlocked_weapons]
    
    for idx, wid in enumerate(weapons_list):
        info = GUNS_DATA[wid]
        card_y = py + 115 + idx * 74
        card_rect = pygame.Rect(px + 40, card_y, 440, 66)
        
        is_unlocked = True
        is_equipped = (wid in equipped_weapons)
        
        # Thiết lập màu sắc thẻ dựa trên trạng thái
        if is_equipped:
            bg_color = (40, 30, 15)
            border_color = (255, 150, 0)
            text_color = WHITE
            tag_text = "SLOT 1" if equipped_weapons.index(wid) == 0 else "SLOT 2"
            tag_color = (100, 255, 120)
        else:
            bg_color = (22, 22, 28)
            border_color = (80, 80, 90)
            text_color = (200, 200, 200)
            tag_text = "MANG THEO"
            tag_color = (180, 180, 180)
            
        # Vẽ thẻ súng
        pygame.draw.rect(surf, bg_color, card_rect, border_radius=6)
        
        # Nếu chuột hover qua, làm nổi bật viền và dịch chuyển ngang sang phải nhẹ cực kỳ mượt mà
        if card_rect.collidepoint(mouse_pos):
            pygame.draw.rect(surf, (255, 215, 0), card_rect, 2, border_radius=6)
            card_offset_x = 8
        else:
            pygame.draw.rect(surf, border_color, card_rect, 1, border_radius=6)
            card_offset_x = 0
            
        # Vẽ súng từ bộ nhớ đệm Cache (tối ưu hóa 100% mượt mà, không load từ đĩa liên tục)
        if wid in _backpack_image_cache:
            g_img = _backpack_image_cache[wid]
            if g_img:
                surf.blit(g_img, (px + 55 + card_offset_x, card_y + 15))
        else:
            gun_img_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"{wid}.png")
            g_img = None
            if os.path.exists(gun_img_path):
                try:
                    loaded_img = pygame.image.load(gun_img_path).convert_alpha()
                    bbox = loaded_img.get_bounding_rect()
                    if bbox.width > 0 and bbox.height > 0:
                        loaded_img = loaded_img.subsurface(bbox)
                    g_img = pygame.transform.scale(loaded_img, (70, 35))
                except Exception:
                    pass
            _backpack_image_cache[wid] = g_img
            if g_img:
                surf.blit(g_img, (px + 55 + card_offset_x, card_y + 15))
                
        # Thông tin súng
        draw_text(surf, info['name'], px + 145 + card_offset_x, card_y + 12, 16, text_color, False, None, True)
        draw_text(surf, f"S.Thương: {info['damage']} | T.Bắn: {info['fire_rate']}s", px + 145 + card_offset_x, card_y + 36, 12, (150, 150, 150))
        
        # Nhãn trạng thái bên phải thẻ
        draw_text(surf, tag_text, px + 400 + card_offset_x, card_y + 24, 13, tag_color, True)
        
    # --- CỘT PHẢI: TRANG BỊ KHÁC (Pet đồng hành & Skin) ---
    draw_text(surf, "🐾 THÚ CƯNG ĐỒNG HÀNH (TRANG BỊ 1)", px + 510, py + 85, 16, YELLOW)
    # Lọc chỉ hiện Pet đã mua/sở hữu
    pets_list = [p for p in ['mini_robot', 'plasma_pup', 'lucky_cat'] if p in unlocked_pets]
    
    if not pets_list:
        # Nếu chưa mua Pet nào, vẽ bảng thông báo trống cực kỳ đẹp mắt
        empty_rect = pygame.Rect(px + 500, py + 115, 360, 254)
        pygame.draw.rect(surf, (15, 15, 20), empty_rect, border_radius=6)
        pygame.draw.rect(surf, (80, 45, 15), empty_rect, 1, border_radius=6)
        draw_text(surf, "CHƯA SỞ HỮU THÚ CƯNG NÀO", px + 680, py + 210, 16, (150, 150, 160), True)
        draw_text(surf, "Hãy vào Cửa hàng sắm ngay một Pet đồng hành", px + 680, py + 240, 11, (110, 130, 120), True)
        draw_text(surf, "để gia tăng đáng kể sức mạnh chiến đấu nhé!", px + 680, py + 260, 11, (110, 130, 120), True)
    else:
        for idx, pid in enumerate(pets_list):
            info = PETS_DATA[pid]
            card_y = py + 115 + idx * 88
            card_rect = pygame.Rect(px + 500, card_y, 360, 78)
            
            is_unlocked = True
            is_equipped = (selected_pet == pid)
            
            if is_equipped:
                bg_color = (30, 45, 30)
                border_color = (0, 255, 0)
                text_color = WHITE
                tag_text = "✔ BẬT"
                tag_color = (100, 255, 120)
            else:
                bg_color = (22, 22, 28)
                border_color = (80, 80, 90)
                text_color = (200, 200, 200)
                tag_text = "ĐÃ CÓ"
                tag_color = (180, 180, 180)
                
            pygame.draw.rect(surf, bg_color, card_rect, border_radius=6)
            
            # Hiệu ứng nổi bật khi hover card Pet trong balo
            if card_rect.collidepoint(mouse_pos):
                pygame.draw.rect(surf, (255, 215, 0), card_rect, 2, border_radius=6)
                card_offset_x = 8
            else:
                pygame.draw.rect(surf, border_color, card_rect, 1, border_radius=6)
                card_offset_x = 0
                
            # Tên Pet
            draw_text(surf, info['name'], px + 515 + card_offset_x, card_y + 12, 16, text_color, False, None, True)
            # Mô tả ngắn
            desc_lines = [info['desc'][i:i+40] for i in range(0, len(info['desc']), 40)]
            for l_idx, line in enumerate(desc_lines[:2]):
                draw_text(surf, line, px + 515 + card_offset_x, card_y + 35 + l_idx * 14, 11, (160, 160, 170))
                
            draw_text(surf, tag_text, px + 800 + card_offset_x, card_y + 12, 12, tag_color, True)

    # Hiển thị trang phục nhân vật đang mặc
    skin_y = py + 385
    skin_rect = pygame.Rect(px + 500, skin_y, 360, 80)
    pygame.draw.rect(surf, (20, 25, 35), skin_rect, border_radius=6)
    pygame.draw.rect(surf, (100, 150, 255), skin_rect, 1, border_radius=6)
    
    draw_text(surf, "👕 TRANG PHỤC HIỆN TẠI", px + 515, skin_y + 12, 15, (100, 200, 255), False, None, True)
    
    skin_names = {
        'mu': 'Cristiano Ronaldo - CR7 (Manchester United)',
        'rm': 'Cristiano Ronaldo - CR7 (Real Madrid)',
        'an': 'Cristiano Ronaldo - CR7 (Al Nassr)'
    }
    active_skin_name = skin_names.get(player_skin, 'Cristiano Ronaldo')
    draw_text(surf, active_skin_name, px + 515, skin_y + 36, 13, WHITE)
    draw_text(surf, "Nhấp chọn avatar ở sảnh chờ để đổi trang phục", px + 515, skin_y + 54, 12, (150, 150, 160))

    # --- NÚT ĐÓNG HÀNH TRANG ---
    close_btn = pygame.Rect(WIDTH // 2 - 120, py + 490, 240, 42)
    btn_hover = close_btn.collidepoint(mouse_pos)
    btn_bg = (220, 50, 30) if btn_hover else (150, 30, 20)
    pygame.draw.rect(surf, btn_bg, close_btn, border_radius=6)
    pygame.draw.rect(surf, (255, 120, 0), close_btn, 1, border_radius=6)
    draw_text(surf, "ĐÓNG HÀNH TRANG (ESC)", WIDTH // 2, py + 510, 16, WHITE, True)


def draw_achievements_screen(surf, robots_killed):
    surf.fill((15, 15, 30))
    draw_text(surf, "THÀNH TÍCH", WIDTH // 2, 40, 36, YELLOW, True)
    stats = [
        f"Tổng robot tiêu diệt: {robots_killed}",
        f"Mục tiêu: Tiêu diệt toàn bộ robot + Qua màn 6",
    ]
    for i, s in enumerate(stats):
        draw_text(surf, s, WIDTH // 2, 150 + i * 50, 24, (200, 200, 220), True)
    draw_text(surf, "Nhấn ESC để quay lại", WIDTH // 2, HEIGHT - 50, 18, (150, 150, 180), True)

def draw_hud(surf, player, level_num, robots_left, light_on):
    # Nền HUD
    hud_h = 50
    hud_surf = pygame.Surface((WIDTH, hud_h), pygame.SRCALPHA)
    hud_surf.fill((0, 0, 0, 160))
    surf.blit(hud_surf, (0, 0))

    # HP bar
    bx, by, bw, bh = 10, 10, 150, 16
    pygame.draw.rect(surf, (60, 0, 0), (bx, by, bw, bh), border_radius=4)
    hw = int(bw * player.hp / player.max_hp)
    pygame.draw.rect(surf, (220, 40, 40), (bx, by, hw, bh), border_radius=4)
    pygame.draw.rect(surf, (255, 100, 100), (bx, by, bw, bh), 1, border_radius=4)
    draw_text(surf, f"HP: {int(player.hp)}", bx + 5, by, 14, WHITE)

    # Energy bar
    ey = by + 20
    pygame.draw.rect(surf, (0, 0, 60), (bx, ey, bw, bh), border_radius=4)
    ew = int(bw * player.energy / player.max_energy)
    pygame.draw.rect(surf, (50, 150, 255), (bx, ey, ew, bh), border_radius=4)
    pygame.draw.rect(surf, (100, 180, 255), (bx, ey, bw, bh), 1, border_radius=4)
    draw_text(surf, f"NL: {int(player.energy)}", bx + 5, ey, 14, WHITE)

    # Đạn dược - Infinite ammo
    ammo_color = ORANGE if player.weapon == 'gun' else (120, 120, 120)
    draw_text(surf, "ĐẠN: ∞", 180, 30, 16, ammo_color)

    # Màn + robot
    draw_text(surf, f"Màn {level_num + 1}: {LEVEL_NAMES[level_num]}", 320, 8, 18, (200, 200, 220))
    draw_text(surf, f"Robot còn: {robots_left}", 320, 28, 16, (255, 150, 150))

    # Đèn icon
    light_color = (255, 255, 100) if light_on else (80, 80, 80)
    pygame.draw.circle(surf, light_color, (WIDTH - 40, 25), 12)
    light_label = "ON" if light_on else "OFF"
    draw_text(surf, light_label, WIDTH - 58, 14, 14, light_color)

    # === HỆ THỐNG SLOT VŨ KHÍ HUD ĐA NĂNG ===
    unlocked_g = getattr(player, 'unlocked_weapons', ['pistol'])
    active_wp = player.weapon  # 'sword' hoặc 'gun'
    active_gun = getattr(player, 'selected_gun', 'pistol')
    
    # Định nghĩa các slot vũ khí
    slots = []
    # Slot L: Kiếm
    slots.append({
        'id': 'sword',
        'key': 'L',
        'name': 'KIẾM',
        'active': (active_wp == 'sword'),
        'color': (200, 200, 220)
    })
    
    # Slot 1: Súng thứ 1 (Pistol)
    if len(unlocked_g) >= 1:
        gun1_id = unlocked_g[0]
        gun1_info = GUNS_DATA.get(gun1_id, GUNS_DATA['pistol'])
        slots.append({
            'id': gun1_id,
            'key': '1',
            'name': gun1_info['name'].upper(),
            'active': (active_wp == 'gun' and active_gun == gun1_id),
            'color': gun1_info.get('color', ORANGE)
        })
        
    # Slot 2: Súng thứ 2 (nếu có)
    if len(unlocked_g) >= 2:
        gun2_id = unlocked_g[1]
        gun2_info = GUNS_DATA.get(gun2_id, GUNS_DATA['pistol'])
        slots.append({
            'id': gun2_id,
            'key': '2',
            'name': gun2_info['name'].upper(),
            'active': (active_wp == 'gun' and active_gun == gun2_id),
            'color': gun2_info.get('color', ORANGE)
        })

    # Vẽ từng slot
    start_x = WIDTH - 365
    box_w, box_h = 75, 34
    gap = 8
    
    for idx, slot in enumerate(slots):
        bx = start_x + idx * (box_w + gap)
        by = 8
        
        # Thiết lập màu sắc và viền cho trạng thái Active / Inactive
        if slot['active']:
            bg_color = (20, 40, 60, 220)
            border_color = (0, 255, 255) # Màu xanh neon rực rỡ cho súng/kiếm đang dùng
            border_width = 2
            text_color = WHITE
        else:
            bg_color = (10, 10, 15, 120)
            border_color = (80, 80, 90)
            border_width = 1
            text_color = (130, 140, 150)
            
        # Vẽ nền hộp vật phẩm
        box_surf = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        box_surf.fill(bg_color)
        surf.blit(box_surf, (bx, by))
        
        # Vẽ viền hộp
        pygame.draw.rect(surf, border_color, (bx, by, box_w, box_h), border_width, border_radius=3)
        
        # Vẽ phím phím tắt ở góc trên bên trái
        draw_text(surf, slot['key'], bx + 4, by + 1, 10, border_color)
        
        # Vẽ biểu tượng vũ khí bên trong
        if slot['id'] == 'sword':
            # Vẽ thanh kiếm nghiêng nhỏ
            pygame.draw.line(surf, slot['color'], (bx + box_w - 20, by + 8), (bx + 24, by + box_h - 8), 2)
            pygame.draw.circle(surf, (200, 180, 130), (bx + 24, by + box_h - 8), 2)
        else:
            # Vẽ ảnh súng thật
            gid = slot['id']
            img_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"{gid}.png")
            drawn_img = False
            if os.path.exists(img_path):
                try:
                    if not hasattr(draw_hud, '_hud_gun_slots_cache'):
                        draw_hud._hud_gun_slots_cache = {}
                    cache_key = (gid, slot['active'])
                    if cache_key not in draw_hud._hud_gun_slots_cache:
                        g_img = pygame.image.load(img_path).convert_alpha()
                        g_img = pygame.transform.scale(g_img, (32, 16))
                        if not slot['active']:
                            g_img.set_alpha(150)
                        draw_hud._hud_gun_slots_cache[cache_key] = g_img
                    
                    hud_img = draw_hud._hud_gun_slots_cache[cache_key]
                    surf.blit(hud_img, (bx + box_w - 38, by + 6))
                    drawn_img = True
                except Exception:
                    pass
            if not drawn_img:
                # Vẽ vector súng nhỏ thay thế
                pygame.draw.line(surf, YELLOW, (bx + 25, by + 18), (bx + 45, by + 12), 2)
                
        # Tên viết tắt của vũ khí
        name_label = slot['name']
        if len(name_label) > 10:
            name_label = name_label[:9] + "."
        draw_text(surf, name_label, bx + 4, by + box_h - 13, 9, text_color)

def draw_game_over(surf, selected):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 190))
    surf.blit(overlay, (0, 0))
    
    # Title
    t = pygame.time.get_ticks()
    pulse_red = (200 + int(math.sin(t / 150) * 55), 30, 30)
    draw_text(surf, "GAME OVER", WIDTH // 2, HEIGHT // 2 - 90, 56, pulse_red, True)
    draw_text(surf, "Bạn đã gục ngã trong bóng tối...", WIDTH // 2, HEIGHT // 2 - 30, 24, (200, 200, 220), True)
    
    # Options box centered
    options = ["CHƠI LẠI", "QUAY LẠI"]
    for i, opt in enumerate(options):
        # Vẽ nút nằm ngang
        x = WIDTH // 2 - 120 + i * 160
        y = HEIGHT // 2 + 30
        is_sel = (i == selected)
        
        # Button background
        bg_col = (50, 20, 20) if is_sel else (30, 30, 35)
        border_col = RED if is_sel else (80, 80, 90)
        text_col = WHITE if is_sel else (160, 160, 170)
        
        btn_rect = pygame.Rect(x - 70, y - 18, 140, 40)
        pygame.draw.rect(surf, bg_col, btn_rect, border_radius=8)
        pygame.draw.rect(surf, border_col, btn_rect, 2, border_radius=8)
        
        # Glow effect for selection
        if is_sel:
            glow = pygame.Surface((148, 48), pygame.SRCALPHA)
            pygame.draw.rect(glow, (255, 50, 50, 25), (0, 0, 148, 48), border_radius=10)
            surf.blit(glow, (x - 74, y - 22))
            
        draw_text(surf, opt, x, y, 20, text_col, True)
        
    draw_text(surf, "Dùng phím ← → hoặc ↑ ↓ và nhấn ENTER để chọn", WIDTH // 2, HEIGHT // 2 + 105, 14, (120, 120, 140), True)

def draw_pause_menu(surf, selected, lobby_volume=0.25, game_volume=0.28):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))
    surf.blit(overlay, (0, 0))
    
    box_w, box_h = 420, 420
    box_x, box_y = (WIDTH - box_w) // 2, (HEIGHT - box_h) // 2
    
    # Draw Menu container with glow
    pygame.draw.rect(surf, (15, 15, 25), (box_x, box_y, box_w, box_h), border_radius=16)
    pygame.draw.rect(surf, (0, 180, 255), (box_x, box_y, box_w, box_h), 2, border_radius=16)
    
    # Title
    draw_text(surf, "TẠM DỪNG", WIDTH // 2, box_y + 30, 28, (0, 200, 255), True)
    
    # --- 3 NÚT CHỨC NĂNG ---
    options = ["TIẾP TỤC", "CHƠI LẠI", "THOÁT GAME"]
    for i, opt in enumerate(options):
        y = box_y + 80 + i * 50
        is_sel = (i == selected)
        
        bg_col = (10, 40, 60) if is_sel else (25, 25, 35)
        border_col = (0, 200, 255) if is_sel else (60, 60, 70)
        text_col = WHITE if is_sel else (170, 170, 180)
        
        btn_rect = pygame.Rect(WIDTH // 2 - 110, y - 18, 220, 36)
        pygame.draw.rect(surf, bg_col, btn_rect, border_radius=8)
        pygame.draw.rect(surf, border_col, btn_rect, 2, border_radius=8)
        
        if is_sel:
            glow = pygame.Surface((228, 44), pygame.SRCALPHA)
            pygame.draw.rect(glow, (0, 180, 255, 20), (0, 0, 228, 44), border_radius=10)
            surf.blit(glow, (WIDTH // 2 - 114, y - 22))
            
        draw_text(surf, opt, WIDTH // 2, y, 18, text_col, True)

    # --- ĐƯỜNG KẺ PHÂN TÁCH ---
    sep_y = box_y + 230
    pygame.draw.line(surf, (0, 120, 180, 100), (box_x + 30, sep_y), (box_x + box_w - 30, sep_y), 1)
    draw_text(surf, "🔊 ÂM LƯỢNG", WIDTH // 2, sep_y + 12, 14, (0, 180, 255), True)

    # --- SLIDER 1: ÂM THANH SẢNH (index 3) ---
    is_lobby_sel = (selected == 3)
    lobby_label_y = box_y + 255
    slider_x = box_x + 60
    slider_w = box_w - 120
    slider_h = 10
    lobby_slider_y = box_y + 275

    label_col = (0, 220, 255) if is_lobby_sel else (150, 160, 170)
    draw_text(surf, "Nhạc sảnh", slider_x - 5, lobby_label_y, 13, label_col)
    pct_text = f"{int(lobby_volume * 100)}%"
    draw_text(surf, pct_text, slider_x + slider_w + 10, lobby_label_y, 13, YELLOW)

    # Background bar
    pygame.draw.rect(surf, (50, 50, 60), (slider_x, lobby_slider_y, slider_w, slider_h), border_radius=5)
    # Active progress
    lw = int(slider_w * lobby_volume)
    bar_col = (0, 200, 255) if is_lobby_sel else (0, 140, 200)
    pygame.draw.rect(surf, bar_col, (slider_x, lobby_slider_y, lw, slider_h), border_radius=5)
    # Handle
    hx = slider_x + lw
    pygame.draw.circle(surf, WHITE if is_lobby_sel else (180, 180, 190), (hx, lobby_slider_y + 5), 8)
    pygame.draw.circle(surf, bar_col, (hx, lobby_slider_y + 5), 5)
    # Glow khi chọn
    if is_lobby_sel:
        glow_s = pygame.Surface((slider_w + 30, slider_h + 20), pygame.SRCALPHA)
        pygame.draw.rect(glow_s, (0, 180, 255, 25), (0, 0, slider_w + 30, slider_h + 20), border_radius=8)
        surf.blit(glow_s, (slider_x - 15, lobby_slider_y - 10))

    # --- SLIDER 2: ÂM THANH MÀN CHƠI (index 4) ---
    is_game_sel = (selected == 4)
    game_label_y = box_y + 320
    game_slider_y = box_y + 340

    label_col2 = (0, 220, 255) if is_game_sel else (150, 160, 170)
    draw_text(surf, "Nhạc trận", slider_x - 5, game_label_y, 13, label_col2)
    pct_text2 = f"{int(game_volume * 100)}%"
    draw_text(surf, pct_text2, slider_x + slider_w + 10, game_label_y, 13, YELLOW)

    # Background bar
    pygame.draw.rect(surf, (50, 50, 60), (slider_x, game_slider_y, slider_w, slider_h), border_radius=5)
    # Active progress
    gw = int(slider_w * game_volume)
    bar_col2 = (0, 200, 255) if is_game_sel else (0, 140, 200)
    pygame.draw.rect(surf, bar_col2, (slider_x, game_slider_y, gw, slider_h), border_radius=5)
    # Handle
    hx2 = slider_x + gw
    pygame.draw.circle(surf, WHITE if is_game_sel else (180, 180, 190), (hx2, game_slider_y + 5), 8)
    pygame.draw.circle(surf, bar_col2, (hx2, game_slider_y + 5), 5)
    # Glow khi chọn
    if is_game_sel:
        glow_s2 = pygame.Surface((slider_w + 30, slider_h + 20), pygame.SRCALPHA)
        pygame.draw.rect(glow_s2, (0, 180, 255, 25), (0, 0, slider_w + 30, slider_h + 20), border_radius=8)
        surf.blit(glow_s2, (slider_x - 15, game_slider_y - 10))

    # --- HƯỚNG DẪN ---
    draw_text(surf, "↑↓ Chọn  |  ←→ Chỉnh âm lượng  |  ENTER Xác nhận", WIDTH // 2, box_y + box_h - 25, 11, (100, 100, 120), True)

def draw_victory(surf):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))
    surf.blit(overlay, (0, 0))
    # Hiệu ứng vàng
    t = pygame.time.get_ticks()
    c = (255, 200 + int(math.sin(t / 200) * 55), 50)
    draw_text(surf, "VICTORY!", WIDTH // 2, HEIGHT // 2 - 80, 64, c, True)
    draw_text(surf, "ÁNH SÁNG ĐÃ TRỞ LẠI!", WIDTH // 2, HEIGHT // 2 - 10, 36, YELLOW, True)
    draw_text(surf, "Bạn đã giải phóng thế giới khỏi lũ Robot tàn ác!", WIDTH // 2, HEIGHT // 2 + 40, 22, (200, 200, 220), True)
    draw_text(surf, "Nhấn ESC hoặc R để quay về menu", WIDTH // 2, HEIGHT // 2 + 90, 20, (150, 150, 180), True)

def draw_minimap(surf, player, level, bullets, cam_x, cam_y):
    """Vẽ bản đồ con (minimap) hiện đại, sắc nét ở góc dưới bên trái màn hình"""
    # Kích thước minimap
    mm_w, mm_h = 160, 120
    # Vị trí góc dưới bên trái (HEIGHT = 720)
    mm_x, mm_y = 20, HEIGHT - mm_h - 20
    
    # 1. Vẽ nền minimap bán trong suốt có viền bo tròn tinh tế
    mm_surf = pygame.Surface((mm_w, mm_h), pygame.SRCALPHA)
    mm_surf.fill((10, 10, 20, 180))  # Nền tối trong suốt
    pygame.draw.rect(mm_surf, (80, 80, 100), (0, 0, mm_w, mm_h), 2, border_radius=4)  # Viền xám
    
    # Tỷ lệ scale từ bản đồ chính (2400x1800 -> 160x120 => chia 15)
    scale_x = mm_w / level.map_w
    scale_y = mm_h / level.map_h
    
    # 2. Vẽ tường (Walls) màu xám sẫm
    for w in level.walls:
        wx = int(w.x * scale_x)
        wy = int(w.y * scale_y)
        ww = int(w.w * scale_x)
        wh = int(w.h * scale_y)
        pygame.draw.rect(mm_surf, (50, 50, 65), (wx, wy, max(1, ww), max(1, wh)))
        
    # 3. Vẽ vật phẩm (Items) màu sắc lung linh theo cấu hình của chúng
    for item in level.items:
        if item.alive:
            ix = int(item.x * scale_x)
            iy = int(item.y * scale_y)
            pygame.draw.circle(mm_surf, item.color, (ix, iy), 2)
            
    # 4. Vẽ Robot đang hoạt động (màu theo màu thực tế)
    for r in level.robots:
        if r.alive:
            rx = int(r.x * scale_x)
            ry = int(r.y * scale_y)
            pygame.draw.circle(mm_surf, r.color, (rx, ry), 2)
            
    # 5. Vẽ Khung Tầm nhìn của Camera (Viewport)
    cx = int(cam_x * scale_x)
    cy = int(cam_y * scale_y)
    cw = int(WIDTH * scale_x)
    ch = int(HEIGHT * scale_y)
    pygame.draw.rect(mm_surf, (200, 200, 200, 60), (cx, cy, cw, ch), 1)

    # 6. Vẽ Người chơi (CR7) nhấp nháy nổi bật
    if player.alive:
        px = int(player.x * scale_x)
        py = int(player.y * scale_y)
        # Nhấp nháy nhẹ để phân biệt
        pulse = (pygame.time.get_ticks() // 250) % 2
        p_color = YELLOW if pulse else WHITE
        pygame.draw.circle(mm_surf, p_color, (px, py), 3)
        # Hướng đèn pin di chuyển
        angle = player.angle
        lx = px + int(math.cos(angle) * 5)
        ly = py + int(math.sin(angle) * 5)
        pygame.draw.line(mm_surf, p_color, (px, py), (lx, ly), 1)
        
        # Vẽ tia lửa súng bắn (muzzle flash) trên minimap
        if hasattr(player, 'gun_flash_timer') and player.gun_flash_timer > 0:
            f_len = int(4 + 8 * (player.gun_flash_timer / 0.15))
            fx = px + int(math.cos(angle) * f_len)
            fy = py + int(math.sin(angle) * f_len)
            # Đường tia sáng súng màu cam rực
            pygame.draw.line(mm_surf, (255, 120, 0), (px, py), (fx, fy), 2)
            # Điểm sáng lóe đầu nòng màu vàng rực
            pygame.draw.circle(mm_surf, (255, 240, 50), (fx, fy), 3)
        
    # 7. Vẽ các viên đạn đang bay (Tracer bullets) màu cam vàng
    for b in bullets:
        if b.alive:
            bx = int(b.x * scale_x)
            by = int(b.y * scale_y)
            # Vẽ tia đạn nhỏ
            dx = int(math.cos(b.angle) * 3)
            dy = int(math.sin(b.angle) * 3)
            pygame.draw.line(mm_surf, (255, 200, 50), (bx - dx, by - dy), (bx, by), 2)
            pygame.draw.circle(mm_surf, WHITE, (bx, by), 1)
        
    # Vẽ minimap lên màn hình game chính
    surf.blit(mm_surf, (mm_x, mm_y))
    
    # 7. Nhãn chữ tên bản đồ góc trên
    font = _get_font(12)
    txt = font.render("BẢN ĐỒ CON", True, (200, 200, 220))
    surf.blit(txt, (mm_x + 2, mm_y - 18))

def draw_level_intro(surf, level_num, elapsed_ms=0):
    if BG_IMAGE:
        surf.blit(BG_IMAGE, (0, 0))
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 185))
        surf.blit(overlay, (0, 0))
    else:
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        surf.blit(overlay, (0, 0))

    # Fade-in cho từng phần
    fade1 = min(255, int(elapsed_ms / 2))        # Tiêu đề fade-in 0.5s
    fade2 = min(255, max(0, int((elapsed_ms - 400) / 2)))   # Tên màn 
    fade3 = min(255, max(0, int((elapsed_ms - 800) / 2)))   # Robot count
    fade4 = min(255, max(0, int((elapsed_ms - 1200) / 2)))  # Hướng dẫn

    # Scale effect cho tiêu đề
    scale_factor = min(1.0, elapsed_ms / 500)
    title_size = int(48 * scale_factor)
    if title_size > 10:
        draw_text_alpha(surf, f"MÀN {level_num + 1}", WIDTH // 2, HEIGHT // 2 - 50, 
                       max(12, title_size), YELLOW, True, fade1)

    if fade2 > 0:
        draw_text_alpha(surf, LEVEL_NAMES[level_num], WIDTH // 2, HEIGHT // 2 + 10, 28, 
                       (200, 200, 220), True, fade2)

    if fade3 > 0:
        counts = LEVEL_ROBOTS[level_num]
        total = sum(counts.values()) if isinstance(counts, dict) else sum(counts)
        draw_text_alpha(surf, f"Robot: {total}", WIDTH // 2, HEIGHT // 2 + 55, 22, 
                       (255, 150, 150), True, fade3)

    if fade4 > 0:
        t = pygame.time.get_ticks()
        blink = (t // 500) % 2
        if blink or elapsed_ms < 2000:
            draw_text_alpha(surf, "Nhấn phím bất kỳ để bắt đầu", WIDTH // 2, HEIGHT // 2 + 100, 18, 
                           (150, 150, 180), True, fade4)

def draw_intro_screen(surf):
    """Vẽ màn hình giới thiệu trò chơi (vũ khí và vật phẩm) hiện đại, sắc nét"""
    surf.fill((10, 10, 22))

    # Nền vũ trụ nhẹ nhàng
    t = pygame.time.get_ticks()
    for i in range(30):
        px = (i * 153 + int(t * 0.01)) % WIDTH
        py = (i * 87 + int(t * 0.005)) % HEIGHT
        pygame.draw.circle(surf, (40, 40, 60), (px, py), 1)

    # Tiêu đề chính
    draw_text(surf, "GIỚI THIỆU TRÒ CHƠI", WIDTH // 2, 40, 38, YELLOW, True)
    draw_text(surf, "Kho Vũ Khí & Hệ Thống Vật Phẩm Sinh Tồn", WIDTH // 2, 85, 18, (170, 170, 190), True)

    # 1. CỘT TRÁI: VŨ KHÍ MẶC ĐỊNH
    left_rect = pygame.Rect(50, 120, 560, 500)
    # Glassmorphism background
    left_bg = pygame.Surface((560, 500), pygame.SRCALPHA)
    left_bg.fill((20, 25, 45, 190))
    surf.blit(left_bg, (50, 120))
    pygame.draw.rect(surf, (0, 180, 255, 140), left_rect, 2, border_radius=12)

    # Tiêu đề cột trái
    draw_text(surf, "⚔️ VŨ KHÍ MẶC ĐỊNH (DEFAULT)", 80, 140, 24, (0, 200, 255))
    draw_text(surf, "Ban đầu bạn sở hữu cả hai vũ khí này. Nhấn [L] để đổi!", 80, 175, 15, (160, 170, 190))

    # Kiếm vật lý
    pygame.draw.rect(surf, (30, 40, 70), (80, 205, 500, 135), border_radius=8)
    pygame.draw.rect(surf, (100, 200, 255, 60), (80, 205, 500, 135), 1, border_radius=8)
    
    # Vẽ icon kiếm nhỏ mô phỏng
    pygame.draw.line(surf, (200, 220, 255), (105, 310), (135, 220), 4)
    pygame.draw.line(surf, (255, 200, 50), (100, 305), (110, 315), 3) # crossguard
    pygame.draw.circle(surf, WHITE, (100, 305), 3) # gem
    
    draw_text(surf, "KIẾM THÉP VẬT LÝ", 160, 215, 20, WHITE)
    draw_text(surf, "• Loại: Vũ khí cận chiến", 160, 245, 15, (200, 200, 220))
    draw_text(surf, "• Sát thương: 18 HP / nhát chém", 160, 265, 15, (200, 200, 220))
    draw_text(surf, "• Góc quét: 120 độ chém lan rộng rãi trước mặt", 160, 285, 15, (200, 200, 220))
    draw_text(surf, "⭐ Đặc điểm: Không tốn năng lượng, chém lan nhiều mục tiêu cực mạnh!", 160, 310, 14, YELLOW)

    # Súng lục
    pygame.draw.rect(surf, (30, 40, 70), (80, 360, 500, 135), border_radius=8)
    pygame.draw.rect(surf, (100, 200, 255, 60), (80, 360, 500, 135), 1, border_radius=8)
    
    # Vẽ icon súng lục nhỏ mô phỏng
    pygame.draw.line(surf, (150, 150, 160), (100, 435), (130, 435), 6) # slide
    pygame.draw.line(surf, (120, 120, 130), (102, 435), (102, 455), 5) # grip
    pygame.draw.circle(surf, ORANGE, (132, 435), 3) # muzzle
    
    draw_text(surf, "SÚNG LỤC NĂNG LƯỢNG", 160, 370, 20, WHITE)
    draw_text(surf, "• Loại: Vũ khí tầm xa", 160, 400, 15, (200, 200, 220))
    draw_text(surf, "• Sát thương: 25 HP / viên đạn (Tốc bắn: 0.5s)", 160, 420, 15, (200, 200, 220))
    draw_text(surf, "• Băng đạn: 10 viên (Kho đạn dự trữ tối đa 99 viên)", 160, 440, 15, (200, 200, 220))
    draw_text(surf, "• Phím bắn: [J]  |  Nạp đạn: Nhấn [R] (mất 1.2s)", 160, 460, 15, (200, 200, 220))
    draw_text(surf, "⭐ Đặc điểm: Tấn công tầm xa cực kỳ an toàn & chính xác!", 160, 485, 14, YELLOW)

    # Mẹo chiến đấu
    draw_text(surf, "💡 Mẹo: Chém kiếm khi robot lại gần để tiết kiệm đạn, và dùng súng", 80, 515, 15, (0, 230, 150))
    draw_text(surf, "để bắn tỉa robot từ xa trước khi chúng tiếp cận bạn!", 80, 535, 15, (0, 230, 150))


    # 2. CỘT PHẢI: HỆ THỐNG VẬT PHẨM
    right_rect = pygame.Rect(670, 120, 560, 500)
    # Glassmorphism background
    right_bg = pygame.Surface((560, 500), pygame.SRCALPHA)
    right_bg.fill((20, 25, 45, 190))
    surf.blit(right_bg, (670, 120))
    pygame.draw.rect(surf, (255, 215, 0, 140), right_rect, 2, border_radius=12)

    # Tiêu đề cột phải
    draw_text(surf, "🎒 HỆ THỐNG VẬT PHẨM (ITEMS)", 700, 140, 24, (255, 215, 0))
    draw_text(surf, "Vật phẩm rơi ngẫu nhiên trên map hoặc khi tiêu diệt Robot (30%):", 700, 175, 15, (190, 180, 160))

    # Grid các vật phẩm
    items_to_draw = [
        ('battery', 'PIN (NL)', 'Hồi +32 năng lượng ngay lập tức để sử dụng kỹ năng.', (0, 200, 0)),
        ('medkit', 'MÁU (HP)', 'Hồi +22 máu (HP), giúp bạn sống sót khi bị vây ráp.', (255, 80, 80)),
        ('bulb', 'BÓNG ĐÈN', 'Nạp +20 năng lượng cho gậy phát sáng của bạn.', (255, 255, 100)),
        ('shoes', 'GIÀY TỐC ĐỘ', 'Tăng +30% tốc độ di chuyển cực nhanh trong vòng 5 giây.', (100, 200, 255)),
        ('magnet', 'NAM CHÂM', 'Tự động hút toàn bộ vật phẩm xung quanh lại gần trong 10 giây.', (200, 50, 50)),
        ('wave', 'SÓNG ĐẨY', 'Đẩy lùi toàn bộ robot xung quanh ra xa để thoát hiểm.', (50, 150, 255)),
        ('ammo', 'ĐẠN DỰ TRỮ', 'Bổ sung +12 đạn vào kho dự trữ súng lục năng lượng.', (255, 150, 50))
    ]

    for idx, (itype, name, desc, color) in enumerate(items_to_draw):
        row = idx // 2
        col = idx % 2
        
        # Tọa độ card vật phẩm
        cx = 700 + col * 260
        cy = 205 + row * 100
        
        # Card background
        pygame.draw.rect(surf, (35, 40, 70), (cx, cy, 240, 85), border_radius=8)
        pygame.draw.rect(surf, (*color, 60), (cx, cy, 240, 85), 1, border_radius=8)
        
        # Vẽ vòng tròn và icon nhỏ của vật phẩm
        ix = cx + 25
        iy = cy + 42
        pygame.draw.circle(surf, color, (ix, iy), 12, 1)
        pygame.draw.circle(surf, WHITE, (ix, iy), 10)
        
        # Vẽ biểu tượng đơn giản cho từng loại vật phẩm
        if itype == 'battery':
            pygame.draw.rect(surf, (0, 180, 0), (ix - 3, iy - 3, 6, 7), border_radius=1)
            pygame.draw.rect(surf, (120, 120, 120), (ix - 1, iy - 5, 2, 2))
        elif itype == 'medkit':
            pygame.draw.rect(surf, (220, 40, 40), (ix - 1, iy - 5, 2, 10))
            pygame.draw.rect(surf, (220, 40, 40), (ix - 5, iy - 1, 10, 2))
        elif itype == 'bulb':
            pygame.draw.circle(surf, (255, 215, 0), (ix, iy - 1), 4)
        elif itype == 'shoes':
            pygame.draw.polygon(surf, (0, 180, 255), [(ix - 4, iy - 4), (ix, iy), (ix - 4, iy + 4)])
        elif itype == 'magnet':
            pygame.draw.arc(surf, (200, 30, 30), (ix - 3, iy - 3, 6, 6), math.pi, 0, 2)
        elif itype == 'wave':
            pygame.draw.circle(surf, (0, 100, 255), (ix, iy), 5, 1)
        elif itype == 'ammo':
            pygame.draw.rect(surf, (218, 165, 32), (ix - 2, iy - 2, 4, 6), border_radius=1)

        # Tên vật phẩm
        draw_text(surf, name, cx + 45, cy + 10, 15, color)
        
        # Mô tả vật phẩm (tách làm 2 dòng nếu dài)
        desc_words = desc.split()
        line1 = " ".join(desc_words[:4])
        line2 = " ".join(desc_words[4:])
        draw_text(surf, line1, cx + 45, cy + 30, 12, (180, 180, 200))
        if line2:
            draw_text(surf, line2, cx + 45, cy + 48, 12, (180, 180, 200))

    # 3. CHÚ THÍCH PHÍM QUAY LẠI
    draw_text(surf, "Nhấn ESC để quay lại menu sảnh chờ", WIDTH // 2, HEIGHT - 45, 16, (140, 140, 170), True)

def draw_settings_screen(surf, lobby_volume, game_volume, settings_tab='sound', settings_sel=0):
    """Vẽ màn hình Cài Đặt (Settings Screen) với thiết kế hiện đại, premium bậc nhất"""
    surf.fill((12, 8, 5))  # Nền tối đất bụi bặm kiểu game sinh tồn quân sự

    # Vẽ ô lưới mờ màu cam rỉ sét hổ phách ở background
    t = pygame.time.get_ticks()
    for x in range(0, WIDTH, 40):
        pygame.draw.line(surf, (60, 25, 10, 40), (x, 0), (x, HEIGHT))
    for y in range(0, HEIGHT, 40):
        pygame.draw.line(surf, (60, 25, 10, 40), (0, y), (WIDTH, y))

    # Lớp phủ vignette tối góc hổ phách phát sáng
    glow_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    pygame.draw.rect(glow_surf, (255, 95, 0, 10), (0, 0, WIDTH, HEIGHT))
    surf.blit(glow_surf, (0, 0))
    
    # Vệt quét radar
    scan_y = (t // 6) % HEIGHT
    scanline = pygame.Surface((WIDTH, 3), pygame.SRCALPHA)
    scanline.fill((255, 95, 0, 20))
    surf.blit(scanline, (0, scan_y))

    # Đường viền HUD cam quân đội cứng cáp
    pygame.draw.rect(surf, (255, 95, 0), (30, 95, 1140, 525), 2, border_radius=6)

    # Tiêu đề chính
    draw_text(surf, "CÀI ĐẶT HỆ THỐNG", WIDTH // 2, 25, 32, (255, 120, 0), True, "press_start_2p.ttf")
    draw_text(surf, "Thiết lập cấu hình âm thanh & phím điều khiển", WIDTH // 2, 65, 16, (140, 140, 170), True)

    # Nút Đóng (X) góc trên bên phải
    close_rect = pygame.Rect(1110, 35, 40, 40)
    pygame.draw.rect(surf, (60, 20, 15), close_rect, border_radius=6)
    pygame.draw.rect(surf, (255, 95, 0), close_rect, 1, border_radius=6)
    draw_text(surf, "X", 1130, 55, 18, (255, 95, 0), True, "press_start_2p.ttf")

    # --- HỆ THỐNG TABS (ÂM THANH vs ĐIỀU KHIỂN) ---
    # Tab 1: ÂM THANH
    bg_color1 = (220, 50, 30) if settings_tab == 'sound' else (25, 20, 15)
    text_color1 = WHITE if settings_tab == 'sound' else (150, 140, 130)
    pygame.draw.rect(surf, bg_color1, (320, 105, 270, 50), border_radius=4)
    pygame.draw.rect(surf, (255, 120, 0) if settings_tab == 'sound' else (50, 45, 40), (320, 105, 270, 50), 1, border_radius=4)
    draw_text(surf, "🔊 ÂM THANH", 455, 120, 18, text_color1, True)

    # Tab 2: ĐIỀU KHIỂN
    bg_color2 = (220, 50, 30) if settings_tab == 'controls' else (25, 20, 15)
    text_color2 = WHITE if settings_tab == 'controls' else (150, 140, 130)
    pygame.draw.rect(surf, bg_color2, (610, 105, 270, 50), border_radius=4)
    pygame.draw.rect(surf, (255, 120, 0) if settings_tab == 'controls' else (50, 45, 40), (610, 105, 270, 50), 1, border_radius=4)
    draw_text(surf, "🎮 ĐIỀU KHIỂN", 745, 120, 18, text_color2, True)

    # Khung nội dung chính bên dưới
    content_rect = pygame.Rect(50, 170, 1100, 435)
    pygame.draw.rect(surf, (15, 12, 10), content_rect, border_radius=6)
    pygame.draw.rect(surf, (120, 45, 15), content_rect, 1, border_radius=6)

    # Khung la bàn radar trang trí phong cách viễn tưởng
    radar_surf = pygame.Surface((1100, 435), pygame.SRCALPHA)
    # Vẽ góc nhọn trang trí
    b_size = 15
    pygame.draw.lines(radar_surf, (255, 95, 0, 40), False, [(15, 15 + b_size), (15, 15), (15 + b_size, 15)], 2)
    pygame.draw.lines(radar_surf, (255, 95, 0, 40), False, [(1085, 15 + b_size), (1085, 15), (1085 - b_size, 15)], 2)
    pygame.draw.lines(radar_surf, (255, 95, 0, 40), False, [(15, 420 - b_size), (15, 420), (15 + b_size, 420)], 2)
    pygame.draw.lines(radar_surf, (255, 95, 0, 40), False, [(1085, 420 - b_size), (1085, 420), (1085 - b_size, 420)], 2)
    surf.blit(radar_surf, (50, 170))

    if settings_tab == 'sound':
        # --- TAB ÂM THANH ---
        draw_text(surf, "CẤU HÌNH ÂM THANH TRONG GAME", WIDTH // 2, 200, 24, YELLOW, True, "vt323.ttf")
        draw_text(surf, "Dùng chuột click trực tiếp hoặc dùng phím ↑ ↓ chọn slider, ← → để tăng giảm âm lượng", WIDTH // 2, 230, 14, (150, 160, 155), True)

        # 1. ÂM THANH SẢNH (LOBBY MUSIC VOLUME)
        is_lobby_sel = (settings_sel == 0)
        card_lobby_y = 265
        pygame.draw.rect(surf, (40, 25, 15) if is_lobby_sel else (18, 14, 12), (80, card_lobby_y, 1040, 95), border_radius=6)
        pygame.draw.rect(surf, YELLOW if is_lobby_sel else (60, 40, 30), (80, card_lobby_y, 1040, 95), 2 if is_lobby_sel else 1, border_radius=6)
        
        # Nhãn & Icon
        label_color = YELLOW if is_lobby_sel else WHITE
        draw_text(surf, "🎵 Âm thanh sảnh chờ", 110, card_lobby_y + 18, 20, label_color)
        draw_text(surf, "Điều chỉnh âm lượng nhạc nền phát tại sảnh chờ, balo và cửa hàng", 110, card_lobby_y + 50, 12, (150, 150, 150))
        
        # Thanh trượt (Slider) từ X: 450 -> 850 (độ dài 400px)
        slider_x = 450
        slider_y = card_lobby_y + 40
        slider_w = 400
        slider_h = 10
        # Background bar
        pygame.draw.rect(surf, (50, 50, 50), (slider_x, slider_y, slider_w, slider_h), border_radius=5)
        # Active progress bar
        lobby_w = int(slider_w * lobby_volume)
        pygame.draw.rect(surf, (255, 120, 0), (slider_x, slider_y, lobby_w, slider_h), border_radius=5)
        # Handle (Nút tròn trượt)
        handle_x = slider_x + lobby_w
        pygame.draw.circle(surf, WHITE, (handle_x, slider_y + 5), 10)
        pygame.draw.circle(surf, (255, 120, 0), (handle_x, slider_y + 5), 6)
        
        # Số % âm lượng
        draw_text(surf, f"{int(lobby_volume * 100)}%", slider_x + slider_w + 30, slider_y - 2, 20, YELLOW)

        # 2. ÂM THANH MÀN CHƠI (GAME LEVEL MUSIC VOLUME)
        is_game_sel = (settings_sel == 1)
        card_game_y = 385
        pygame.draw.rect(surf, (40, 25, 15) if is_game_sel else (18, 14, 12), (80, card_game_y, 1040, 95), border_radius=6)
        pygame.draw.rect(surf, YELLOW if is_game_sel else (60, 40, 30), (80, card_game_y, 1040, 95), 2 if is_game_sel else 1, border_radius=6)
        
        # Nhãn & Icon
        label_color2 = YELLOW if is_game_sel else WHITE
        draw_text(surf, "⚔️ Âm thanh màn chơi", 110, card_game_y + 18, 20, label_color2)
        draw_text(surf, "Điều chỉnh âm lượng nhạc nền trong các màn chiến đấu (màn 1-6)", 110, card_game_y + 50, 12, (150, 150, 150))
        
        # Thanh trượt (Slider)
        slider_y2 = card_game_y + 40
        pygame.draw.rect(surf, (50, 50, 50), (slider_x, slider_y2, slider_w, slider_h), border_radius=5)
        game_w = int(slider_w * game_volume)
        pygame.draw.rect(surf, (255, 120, 0), (slider_x, slider_y2, game_w, slider_h), border_radius=5)
        handle_x2 = slider_x + game_w
        pygame.draw.circle(surf, WHITE, (handle_x2, slider_y2 + 5), 10)
        pygame.draw.circle(surf, (255, 120, 0), (handle_x2, slider_y2 + 5), 6)
        
        # Số % âm lượng
        draw_text(surf, f"{int(game_volume * 100)}%", slider_x + slider_w + 30, slider_y2 - 2, 20, YELLOW)

        # Chú thích nhỏ dưới cùng
        draw_text(surf, "💡 Mẹo: Có thể click bất kỳ điểm nào trên thanh để set âm lượng tức thì", WIDTH // 2, 530, 14, (0, 200, 150), True)

    elif settings_tab == 'controls':
        # --- TAB ĐIỀU KHIỂN (HƯỚNG DẪN) ---
        draw_text(surf, "PHÍM TẮT ĐIỀU KHIỂN TRONG TRẬN ĐẤU", WIDTH // 2, 190, 22, YELLOW, True, "vt323.ttf")
        
        controls = [
            ("WASD / Phím Mũi Tên", "Di chuyển nhân vật chính (CR7)"),
            ("Chuột Trái / Phím J", "Tấn công (Kiếm chém lan rộng / Bắn súng)"),
            ("Phím L", "Đổi vũ khí nhanh (Kiếm thép ↔ Súng năng lượng)"),
            ("1, 2, G / Cuộn Chuột", "Đổi qua lại các súng mang theo"),
            ("Phím R", "Nạp đạn thủ công (khi súng còn đạn)"),
            ("Phím Shift", "Chạy nhanh tăng +50% tốc độ di chuyển"),
            ("Phím T", "Cắm Đèn Trụ phát sáng dụ quái (-20 NL)"),
            ("Phím Q", "Đèn Choáng quái xanh lá trong tầm (-15 NL)"),
            ("Phím E", "Quét Radar hiện quái mờ trong bóng tối (-10 NL)"),
            ("Phím F", "Xung Sáng tối thượng làm mù tất cả quái (-40 NL)"),
            ("Phím SPACE", "Bật/Tắt đèn pin chiếu sáng quạt (miễn phí)"),
            ("Phím 3", "Bật/Tắt chế độ tự chơi BFS (Autoplay BFS)"),
            ("Phím 4", "Bật/Tắt chế độ tự chơi A* (Autoplay A*)"),
            ("Phím 5", "Bật/Tắt chế độ tự chơi DFS (Autoplay DFS)"),
            ("Phím ESC", "Tạm dừng game để cài đặt / Quay lại Menu sảnh"),
        ]

        # Chia controls làm 2 cột vẽ cho đẹp
        col_w = 480
        col_gap = 60
        start_cx = WIDTH // 2 - col_w - col_gap // 2 + 10
        start_cy = 215
        
        for idx, (key, desc) in enumerate(controls):
            row = idx % 8
            col = idx // 8
            
            x = start_cx + col * (col_w + col_gap)
            y = start_cy + row * 47
            
            # Khung con đựng phím tắt
            pygame.draw.rect(surf, (22, 18, 16), (x, y, col_w, 38), border_radius=4)
            pygame.draw.rect(surf, (60, 35, 20), (x, y, col_w, 38), 1, border_radius=4)
            
            # Vẽ phím tắt
            draw_text(surf, key, x + 15, y + 8, 13, (100, 200, 255), False, None, True)
            # Vẽ mô tả
            draw_text(surf, desc, x + 175, y + 10, 11, (200, 200, 210))

    # Hướng dẫn thoát dưới cùng màn hình
    draw_text(surf, "Nhấn ESC hoặc ấn biểu tượng (X) để lưu cài đặt & quay lại sảnh chính", WIDTH // 2, HEIGHT - 35, 15, (120, 140, 130), True)
