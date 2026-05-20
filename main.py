"""Stick Survivor – CR7: Đường về nhà - Main Game"""
import pygame, sys, math, random, json, os
from constants import *
from entities import Player, Robot, Bullet, Item, Particle, PlantedLight
from levels import Level
from ui import *
try:
    from pathfinder import bfs as pf_bfs, astar as pf_astar
except ImportError:
    pf_bfs = pf_astar = None

# Tự động sao chép các ảnh vũ khí mới tải về vào thư mục game
try:
    import shutil
    _brain_dir = r"C:\Users\LENOVO\.gemini\antigravity\brain\b965e400-f776-435f-bd61-c41cdb30fc25"
    _dest_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Khôi phục ảnh weapon_ui.png gốc (Đã tắt để không đè lên ảnh mới của người dùng)
    # _backup_src = os.path.join(_brain_dir, ".tempmediaStorage", "media_b965e400-f776-435f-bd61-c41cdb30fc25_1779209190656.png")
    # if os.path.exists(_backup_src):
    #     for _old_file in ["weapon_ui.png", "weapon_ui_backup.png"]:
    #         _dest_old_path = os.path.join(_dest_dir, _old_file)
    #         shutil.copy(_backup_src, _dest_old_path)
            
    _mapping = {
        "media__1779207651718.png": "pistol.png",
        "media__1779207657799.png": "shotgun.png",
        "media__1779207911074.png": "smg.png",
        "media__1779207920132.png": "sniper.png",
        "media__1779207924813.png": "advanced_sniper.png"
    }
    for _src_name, _dest_name in _mapping.items():
        _src_path = os.path.join(_brain_dir, _src_name)
        _dest_path = os.path.join(_dest_dir, _dest_name)
        if os.path.exists(_src_path):
            shutil.copy(_src_path, _dest_path)
            
    # Nạp lại ảnh bảng trang bị mới trực tiếp vào biến toàn cục của module ui
    import ui
    _ui_path = os.path.join(_dest_dir, 'weapon_ui.png')
    if os.path.exists(_ui_path):
        ui.WEAPON_UI_IMG = pygame.image.load(_ui_path)
except Exception as e:
    pass

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Ngọn Đèn Cuối Cùng")
clock = pygame.time.Clock()

class Game:
    # Đường dẫn file lưu tiến trình (cùng thư mục với main.py)
    SAVE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'save_data.json')

    def __init__(self):
        self.state = 'story'  # Bắt đầu từ phần cốt truyện mở đầu
        self.menu_sel = 0
        self.level_sel = 0  # Lựa chọn trong menu chọn màn
        self.robots_killed = 0
        self.level_num = 0
        self.levels_unlocked = 1  # Số màn đã mở khóa (mặc định = 1, tức chỉ màn 1)
        self.player = None
        self.level = None
        self.bullets = []
        self.enemy_bullets = []  # Đạn robot bắn về phía người chơi
        self.particles = []
        self.planted_lights = []
        self.cam_x = 0
        self.cam_y = 0
        self.scan_timer = 0
        self.scan_active = False
        self.pulse_timer = 0
        self.magnet_timer = 0
        self.level_intro_timer = 0
        self.sandstorm_offset = 0
        self.story_start_tick = pygame.time.get_ticks()
        self.story_all_done = False
        self.level_intro_start_tick = 0
        self.item_spawn_timer = 0
        self.shoot_cd = 0  # Cooldown bắn đạn (0.5 giây)
        self.pause_sel = 0
        self.gameover_sel = 0
        self.player_skin = 'mu'
        self.infinite_ammo = True  # Enable infinite ammo for player
        
        # Hệ thống cửa hàng vũ khí & Pet
        self.unlocked_weapons = ['pistol']
        self.equipped_weapons = ['pistol']
        self.selected_weapon = 'pistol'
        self.coins = 0
        self.preview_weapon = 'pistol'
        self.shop_error_timer = 0.0
        
        self.unlocked_pets = []
        self.selected_pet = None
        self.shop_tab = 'gun'  # 'gun' hoặc 'pet'
        self.preview_pet = 'mini_robot'

        # Chế độ tự chơi (autoplay)
        self.autoplay_mode = None   # None | 'bfs' | 'astar'
        self.autoplay_path = []     # Danh sách waypoints hiện tại
        self.autoplay_timer = 0.0   # Timer tính lại đường

        # Tải tiến trình đã lưu từ file
        self._load_progress()

        # Tải nhạc sảnh chờ
        self.music_loaded = False
        try:
            pygame.mixer.init()
            music_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "new_bg_music.mp3")
            if os.path.exists(music_path):
                pygame.mixer.music.load(music_path)
                pygame.mixer.music.set_volume(0.25)
                self.music_loaded = True
        except Exception:
            pass

        # Tải âm thanh lướt qua (điều hướng)
        self.nav_sound = None
        try:
            nav_sound_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ting.wav")
            if os.path.exists(nav_sound_path):
                self.nav_sound = pygame.mixer.Sound(nav_sound_path)
                self.nav_sound.set_volume(0.2)
        except Exception as e:
            print(f"[WARN] Không thể tải âm thanh điều hướng: {e}")

        self.accept_sound = None
        try:
            accept_sound_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "accept.wav")
            if os.path.exists(accept_sound_path):
                self.accept_sound = pygame.mixer.Sound(accept_sound_path)
                self.accept_sound.set_volume(0.5)
        except Exception as e:
            pass

    def play_nav_sound(self):
        if hasattr(self, 'nav_sound') and self.nav_sound:
            try:
                self.nav_sound.stop()
                self.nav_sound.play()
            except:
                pass

    def play_accept_sound(self):
        if hasattr(self, 'accept_sound') and self.accept_sound:
            try:
                self.accept_sound.stop()
                self.accept_sound.play()
            except:
                pass

    def _load_progress(self):
        """Tải tiến trình đã lưu từ file JSON"""
        if not os.path.exists(self.SAVE_FILE):
            return
        try:
            with open(self.SAVE_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if isinstance(data, dict):
                self.levels_unlocked = max(1, min(6, data.get('levels_unlocked', self.levels_unlocked)))
                self.player_skin = data.get('player_skin', self.player_skin)
                self.unlocked_weapons = data.get('unlocked_weapons', self.unlocked_weapons)
                if not self.unlocked_weapons:
                    self.unlocked_weapons = ['pistol']
                self.equipped_weapons = data.get('equipped_weapons', self.equipped_weapons)
                if not self.equipped_weapons:
                    self.equipped_weapons = ['pistol']
                self.selected_weapon = data.get('selected_weapon', self.selected_weapon)
                self.selected_gun = self.selected_weapon
                self.coins = data.get('coins', self.coins)
                self.unlocked_pets = data.get('unlocked_pets', self.unlocked_pets)
                self.selected_pet = data.get('selected_pet', self.selected_pet)
            print("[INFO] Tải tiến trình thành công từ save_data.json")
        except Exception as e:
            print(f"[WARN] Lỗi khi tải file save: {e}. Sử dụng tiến trình hiện tại.")

    def _save_progress(self):
        """Lưu tiến trình vào file JSON một cách an toàn và ghi đè nguyên tử"""
        try:
            data = {
                'levels_unlocked': self.levels_unlocked,
                'player_skin': self.player_skin,
                'unlocked_weapons': self.unlocked_weapons,
                'equipped_weapons': self.equipped_weapons,
                'selected_weapon': self.selected_weapon,
                'coins': self.coins,
                'unlocked_pets': self.unlocked_pets,
                'selected_pet': self.selected_pet
            }
            temp_file = self.SAVE_FILE + ".tmp"
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            if os.path.exists(self.SAVE_FILE):
                os.remove(self.SAVE_FILE)
            os.rename(temp_file, self.SAVE_FILE)
            print("[INFO] Lưu tiến trình thành công vào save_data.json")
        except Exception as e:
            print(f"[WARN] Không thể lưu tiến trình: {e}")

    def trigger_menu_action(self, idx):
        if idx == 0:
            self.level_sel = 0
            self.state = 'level_select'
        elif idx == 1:
            self.state = 'intro'
        elif idx == 2:
            self.state = 'items'
        elif idx == 3:
            self.state = 'controls'
        elif idx == 4:
            pygame.quit()
            sys.exit()

    def start_level(self, num):
        self.level_num = num
        self.level = Level(num)
        self.player = Player(100, 100)
        self.player.set_skin(self.player_skin)
        self.player.selected_pet = self.selected_pet
        if self.selected_weapon not in self.equipped_weapons:
            self.selected_weapon = self.equipped_weapons[0]
        self.player.selected_gun = self.selected_weapon
        self.player.unlocked_weapons = self.equipped_weapons
        
        # Cấu hình đạn theo vũ khí đã chọn trong Shop súng
        gun_info = GUNS_DATA[self.selected_weapon]
        self.player.max_ammo_clip = gun_info['clip_size']
        self.player.ammo_clip = 9999  # Infinite ammo
        self.player.max_ammo_reserve = 9999
        self.player.ammo_reserve = 9999
        
        self.bullets = []
        self.enemy_bullets = []  # Reset đạn robot mỗi khi vào màn mới
        self.particles = []
        self.planted_lights = []
        self.scan_timer = 0
        self.scan_active = False
        self.pulse_timer = 0
        self.magnet_timer = 0
        self.state = 'level_intro'
        self.level_intro_timer = 0
        self.level_intro_start_tick = pygame.time.get_ticks()
        self.item_spawn_timer = 5.0  # Spawn item đầu tiên sau 5 giây chơi

    def handle_events(self):
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            if self.state == 'story':
                if ev.type == pygame.KEYDOWN:
                    if ev.key == pygame.K_SPACE:
                        if not self.story_all_done:
                            # Nhấn SPACE khi đang chạy chữ: Tua nhanh, hiện toàn bộ chữ ngay lập tức
                            self.story_start_tick = pygame.time.get_ticks() - 30000
                        else:
                            # Chữ đã hiện xong: Nhấn SPACE thêm lần nữa để vào sảnh chờ
                            self.state = 'menu'
                    else:
                        # Các phím khác chỉ được phép chuyển cảnh khi chữ đã hiện xong
                        if self.story_all_done:
                            self.state = 'menu'
                elif ev.type == pygame.MOUSEBUTTONDOWN:
                    # Click chuột chỉ được phép chuyển cảnh khi chữ đã hiện xong
                    if self.story_all_done:
                        self.state = 'menu'
                continue

            if self.state == 'backpack':
                if ev.type == pygame.KEYDOWN:
                    if ev.key == pygame.K_ESCAPE:
                        self.state = 'menu'
                        self._save_progress()
                elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    mx, my = ev.pos
                    self.handle_backpack_click(mx, my)
                continue

            if self.state == 'menu':
                if ev.type == pygame.KEYDOWN:
                    if ev.key == pygame.K_UP:
                        self.menu_sel = (self.menu_sel - 1) % 5
                        self.play_nav_sound()
                    elif ev.key == pygame.K_DOWN:
                        self.menu_sel = (self.menu_sel + 1) % 5
                        self.play_nav_sound()
                    elif ev.key == pygame.K_RETURN:
                        self.play_accept_sound()
                        self.trigger_menu_action(self.menu_sel)
                elif ev.type == pygame.MOUSEMOTION:
                    mx, my = ev.pos
                    rects = get_menu_button_rects()
                    for idx, rect in enumerate(rects):
                        if rect.collidepoint(mx, my):
                            self.menu_sel = idx
                elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    mx, my = ev.pos
                    
                    # Kiểm tra click vào các Avatar chọn skin
                    cy = 65
                    r_av = 30
                    skins_list = ['mu', 'rm', 'an']
                    clicked_avatar = False
                    for idx, skin_id in enumerate(skins_list):
                        cx = 60 + idx * 72
                        if math.hypot(mx - cx, my - cy) <= r_av + 5:
                            self.player_skin = skin_id
                            self.play_accept_sound()
                            self._save_progress()
                            self._spawn_particles(cx, cy, (255, 215, 0), 10)
                            clicked_avatar = True
                            break
                    
                    if not clicked_avatar:
                        # Kiểm tra click vào Bảng trang bị / Balo ở sảnh chờ
                        target_w = 380
                        target_h = 223
                        wx = WIDTH - target_w - 120
                        wy = HEIGHT // 2 - target_h // 2 + 70
                        panel_rect = pygame.Rect(wx, wy, target_w, target_h)
                        
                        if panel_rect.collidepoint(mx, my):
                            self.state = 'backpack'
                            self.play_accept_sound()
                            self.backpack_anim_ticks = pygame.time.get_ticks()
                            self._spawn_particles(mx, my, (255, 120, 0), 15)
                        else:
                            rects = get_menu_button_rects()
                            for idx, rect in enumerate(rects):
                                if rect.collidepoint(mx, my):
                                    self.play_accept_sound()
                                    self.trigger_menu_action(idx)
                continue

            if self.state == 'level_select':
                if ev.type == pygame.KEYDOWN:
                    if ev.key == pygame.K_ESCAPE:
                        self.state = 'menu'
                    elif ev.key == pygame.K_UP or ev.key == pygame.K_LEFT:
                        self.level_sel = (self.level_sel - 1) % 6
                        self.play_nav_sound()
                    elif ev.key == pygame.K_DOWN or ev.key == pygame.K_RIGHT:
                        self.level_sel = (self.level_sel + 1) % 6
                        self.play_nav_sound()
                    elif ev.key == pygame.K_RETURN:
                        if self.level_sel < self.levels_unlocked:
                            self.play_accept_sound()
                            self.robots_killed = 0
                            self.start_level(self.level_sel)
                continue

            if self.state in ('controls', 'achievements', 'intro'):
                if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                    self.state = 'menu'
                continue

            if self.state == 'items':
                if ev.type == pygame.KEYDOWN:
                    if ev.key == pygame.K_TAB:
                        # Nhấn TAB để cộng 9999 vàng
                        self.coins += 9999
                        self._save_progress()
                        self._spawn_particles(640, 65, (255, 215, 0), 30)
                    elif ev.key == pygame.K_ESCAPE:
                        self.state = 'menu'
                    elif ev.key in (pygame.K_LEFT, pygame.K_RIGHT):
                        # Trái/Phải đổi tab
                        self.shop_tab = 'pet' if self.shop_tab == 'gun' else 'gun'
                        self._spawn_particles(600, 130, (255, 120, 0), 12)
                        self.play_nav_sound()
                    elif ev.key == pygame.K_UP:
                        self.play_nav_sound()
                        # Di chuyển lên trong danh sách
                        if self.shop_tab == 'gun':
                            weapons_list = ['pistol', 'shotgun', 'smg', 'sniper', 'advanced_sniper']
                            try:
                                idx = weapons_list.index(self.preview_weapon)
                                next_idx = (idx - 1) % len(weapons_list)
                                self.preview_weapon = weapons_list[next_idx]
                                card_y = 205 + next_idx * 76
                                self._spawn_particles(300, card_y + 34, (255, 120, 0), 8)
                            except ValueError:
                                self.preview_weapon = 'pistol'
                        elif self.shop_tab == 'pet':
                            pets_list = ['mini_robot', 'plasma_pup', 'lucky_cat']
                            try:
                                idx = pets_list.index(self.preview_pet)
                                next_idx = (idx - 1) % len(pets_list)
                                self.preview_pet = pets_list[next_idx]
                                card_y = 205 + next_idx * 130
                                self._spawn_particles(300, card_y + 65, (255, 100, 255), 8)
                            except ValueError:
                                self.preview_pet = 'mini_robot'
                    elif ev.key == pygame.K_DOWN:
                        self.play_nav_sound()
                        # Di chuyển xuống trong danh sách
                        if self.shop_tab == 'gun':
                            weapons_list = ['pistol', 'shotgun', 'smg', 'sniper', 'advanced_sniper']
                            try:
                                idx = weapons_list.index(self.preview_weapon)
                                next_idx = (idx + 1) % len(weapons_list)
                                self.preview_weapon = weapons_list[next_idx]
                                card_y = 205 + next_idx * 76
                                self._spawn_particles(300, card_y + 34, (255, 120, 0), 8)
                            except ValueError:
                                self.preview_weapon = 'pistol'
                        elif self.shop_tab == 'pet':
                            pets_list = ['mini_robot', 'plasma_pup', 'lucky_cat']
                            try:
                                idx = pets_list.index(self.preview_pet)
                                next_idx = (idx + 1) % len(pets_list)
                                self.preview_pet = pets_list[next_idx]
                                card_y = 205 + next_idx * 130
                                self._spawn_particles(300, card_y + 65, (255, 100, 255), 8)
                            except ValueError:
                                self.preview_pet = 'mini_robot'
                    elif ev.key in (pygame.K_RETURN, pygame.K_SPACE):
                        # Enter hoặc Space để mua hoặc trang bị
                        self.buy_or_equip_previewed()
                        
                elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    mx, my = ev.pos
                    
                    # 1. Kiểm tra click vào TABS ở trên cùng hoặc nút Đóng (X)
                    if 35 <= my <= 75 and 1110 <= mx <= 1150:
                        # Nút Đóng (X) góc trên bên phải
                        self.state = 'menu'
                        self._spawn_particles(mx, my, (255, 100, 0), 10)
                    elif 105 <= my <= 155:
                        if 320 <= mx <= 590:
                            self.shop_tab = 'gun'
                            self._spawn_particles(mx, my, (255, 120, 0), 8)
                        elif 610 <= mx <= 880:
                            self.shop_tab = 'pet'
                            self._spawn_particles(mx, my, (255, 120, 0), 8)
                        elif 260 <= mx <= 300:
                            # Nút mũi tên Trái
                            self.shop_tab = 'pet' if self.shop_tab == 'gun' else 'gun'
                            self._spawn_particles(mx, my, (255, 120, 0), 10)
                        elif 900 <= mx <= 940:
                            # Nút mũi tên Phải
                            self.shop_tab = 'pet' if self.shop_tab == 'gun' else 'gun'
                            self._spawn_particles(mx, my, (255, 120, 0), 10)
                    
                    # 2. Kiểm tra click vào danh sách bên trái
                    elif 80 <= mx <= 550:
                        if self.shop_tab == 'gun':
                            weapons_list = ['pistol', 'shotgun', 'smg', 'sniper', 'advanced_sniper']
                            for idx, wid in enumerate(weapons_list):
                                card_y = 205 + idx * 76
                                if card_y <= my <= card_y + 68:
                                    self.preview_weapon = wid
                                    self._spawn_particles(mx, my, (255, 120, 0), 6)
                        elif self.shop_tab == 'pet':
                            pets_list = ['mini_robot', 'plasma_pup', 'lucky_cat']
                            for idx, pid in enumerate(pets_list):
                                card_y = 205 + idx * 130
                                if card_y <= my <= card_y + 120:
                                    self.preview_pet = pid
                                    self._spawn_particles(mx, my, (255, 100, 255), 6)
                                    
                    # 3. Kiểm tra click vào nút mua/trang bị ở bên cột phải (Tọa độ nút mua: X từ 650 đến 1100, Y từ 550 đến 615)
                    elif 650 <= mx <= 1100 and 550 <= my <= 615:
                        self.buy_or_equip_previewed()
                continue

            if self.state == 'level_intro':
                if ev.type == pygame.KEYDOWN or ev.type == pygame.MOUSEBUTTONDOWN:
                    self.state = 'playing'
                continue

            if self.state == 'gameover':
                if ev.type == pygame.KEYDOWN:
                    if ev.key in (pygame.K_LEFT, pygame.K_UP):
                        self.gameover_sel = (self.gameover_sel - 1) % 2
                        self.play_nav_sound()
                    elif ev.key in (pygame.K_RIGHT, pygame.K_DOWN):
                        self.gameover_sel = (self.gameover_sel + 1) % 2
                        self.play_nav_sound()
                    elif ev.key == pygame.K_RETURN:
                        self.play_accept_sound()
                        if self.gameover_sel == 0:  # CHƠI LẠI
                            self.robots_killed = 0
                            self.start_level(self.level_num)
                        else:  # QUAY LẠI
                            self.state = 'menu'; self.menu_sel = 0
                continue

            if self.state == 'victory':
                if ev.type == pygame.KEYDOWN and ev.key == pygame.K_r:
                    self.state = 'menu'; self.menu_sel = 0
                continue

            if self.state == 'paused':
                if ev.type == pygame.KEYDOWN:
                    if ev.key == pygame.K_ESCAPE:
                        self.state = 'playing'
                    elif ev.key == pygame.K_UP:
                        self.pause_sel = (self.pause_sel - 1) % 3
                        self.play_nav_sound()
                    elif ev.key == pygame.K_DOWN:
                        self.pause_sel = (self.pause_sel + 1) % 3
                        self.play_nav_sound()
                    elif ev.key == pygame.K_RETURN:
                        self.play_accept_sound()
                        if self.pause_sel == 0:  # TIẾP TỤC
                            self.state = 'playing'
                        elif self.pause_sel == 1:  # CHƠI LẠI
                            self.robots_killed = 0
                            self.start_level(self.level_num)
                        elif self.pause_sel == 2:  # THOÁT GAME
                            self.state = 'menu'; self.menu_sel = 0
                continue

            if self.state == 'playing':
                if ev.type == pygame.KEYDOWN:
                    if ev.key == pygame.K_ESCAPE:
                        self.state = 'paused'; self.pause_sel = 0; return
                    if ev.key == pygame.K_SPACE:  # Bật/tắt đèn (không tốn năng lượng)
                        self.player.light_on = not self.player.light_on
                    if ev.key == pygame.K_l:  # Đổi vũ khí (kiếm <-> súng)
                        if self.player.weapon == 'sword':
                            self.player.weapon = 'gun'
                        else:
                            self.player.weapon = 'sword'
                        self.player.weapon_switch_timer = 0.3
                        # Hủy trạng thái nạp đạn khi đổi vũ khí
                        self.player.is_reloading = False
                        self.player.reload_timer = 0.0
                        self._spawn_particles(self.player.x, self.player.y, (200, 200, 255), 6)
                    if ev.key == pygame.K_1:  # Phím 1 chọn súng thứ nhất
                        if len(self.equipped_weapons) >= 1:
                            self.switch_active_gun(self.equipped_weapons[0])
                    if ev.key == pygame.K_2:  # Phím 2 chọn súng thứ hai (nếu có)
                        if len(self.equipped_weapons) >= 2:
                            self.switch_active_gun(self.equipped_weapons[1])
                    if ev.key == pygame.K_g:  # Phím G hoán đổi nhanh giữa các súng
                        if len(self.equipped_weapons) >= 2:
                            curr_idx = self.equipped_weapons.index(self.selected_weapon)
                            next_idx = (curr_idx + 1) % len(self.equipped_weapons)
                            self.switch_active_gun(self.equipped_weapons[next_idx])
                    # Keyboard shooting disabled – chỉ bắn bằng chuột trái
                    # if ev.key == pygame.K_j:  # Tấn công (J)
                    #     self.trigger_attack()
                    if ev.key == pygame.K_3:  # Phím 3 – BFS auto-play
                        if self.autoplay_mode == 'bfs':
                            self.autoplay_mode = None
                            self.autoplay_path = []
                        else:
                            self.autoplay_mode = 'bfs'
                            self.autoplay_path = []
                            self.player.light_on = True
                    if ev.key == pygame.K_4:  # Phím 4 – A* auto-play
                        if self.autoplay_mode == 'astar':
                            self.autoplay_mode = None
                            self.autoplay_path = []
                        else:
                            self.autoplay_mode = 'astar'
                            self.autoplay_path = []
                            self.player.light_on = True
                    if ev.key == pygame.K_r:  # Nạp đạn (Reload)
                        if self.player.weapon == 'gun' and not self.player.is_reloading:
                            if self.player.ammo_clip < self.player.max_ammo_clip:
                                if self.player.ammo_reserve > 0:
                                    self.player.is_reloading = True
                                    gun_info = GUNS_DATA[self.selected_weapon]
                                    self.player.reload_timer = gun_info['reload_time']
                                    self._spawn_particles(self.player.x, self.player.y, CYAN, 6)
                                else:
                                    # Không còn đạn dự trữ
                                    self._spawn_particles(self.player.x, self.player.y, RED, 4)
                    if ev.key == pygame.K_t:  # Cắm đèn trụ
                        if self.player.energy >= PLANTED_LIGHT_COST:
                            self.player.energy -= PLANTED_LIGHT_COST
                            self.planted_lights.append(PlantedLight(self.player.x, self.player.y))
                            self._spawn_particles(self.player.x, self.player.y, YELLOW, 8)
                    if ev.key == pygame.K_q:  # Nhấp nháy choáng xanh lá
                        if self.player.energy >= FLASH_COST:
                            self.player.energy -= FLASH_COST
                            for r in self.level.robots:
                                if r.alive and r.rtype == 'green':
                                    d = math.hypot(r.x - self.player.x, r.y - self.player.y)
                                    if d < 200:
                                        r.stun_timer = 2.0
                            self._spawn_particles(self.player.x, self.player.y, (200, 255, 200), 15)
                    if ev.key == pygame.K_e:  # Quét đèn
                        if self.player.energy >= SCAN_COST:
                            self.player.energy -= SCAN_COST
                            self.scan_active = True; self.scan_timer = 1.5
                            self._spawn_particles(self.player.x, self.player.y, CYAN, 12)
                    if ev.key == pygame.K_f:  # Xung sáng
                        if self.player.energy >= PULSE_COST:
                            self.player.energy -= PULSE_COST
                            self.pulse_timer = 0.5
                            for r in self.level.robots:
                                if r.alive:
                                    r.blind_timer = PULSE_BLIND_TIME
                            self._spawn_particles(self.player.x, self.player.y, WHITE, 25)
                elif ev.type == pygame.MOUSEBUTTONDOWN:
                    if ev.button == 1:  # Chuột trái – bắn về hướng hồng tâm
                        mx, my = ev.pos
                        # Chuyển tọa độ màn hình -> thế giới game
                        world_x = mx + self.cam_x
                        world_y = my + self.cam_y
                        # Tính góc từ player tới con chuột
                        angle_to_mouse = math.atan2(world_y - self.player.y, world_x - self.player.x)
                        # Cập nhật góc player để bắn đúng hướng
                        self.player.angle = angle_to_mouse
                        self.trigger_attack()
                    elif ev.button in (4, 5):  # Cuộn chuột đổi súng
                        if len(self.unlocked_weapons) >= 2:
                            curr_idx = self.unlocked_weapons.index(self.selected_weapon)
                            next_idx = (curr_idx + 1) % len(self.unlocked_weapons)
                            self.switch_active_gun(self.unlocked_weapons[next_idx])

    def trigger_attack(self):
        if self.player.weapon == 'sword':
            # === CHÉM KIẾM ===
            if self.shoot_cd <= 0 and self.player.alive:
                self.shoot_cd = SWORD_COOLDOWN
                self.player.sword_swing_timer = SWORD_COOLDOWN
                # Gây sát thương cho robot trong tầm chém
                half_arc = math.radians(SWORD_ARC / 2)
                for r in self.level.robots:
                    if not r.alive: continue
                    d = math.hypot(r.x - self.player.x, r.y - self.player.y)
                    if d < SWORD_RANGE + r.radius:
                        angle_to = math.atan2(r.y - self.player.y, r.x - self.player.x)
                        diff = abs(angle_to - self.player.angle)
                        if diff > math.pi: diff = 2 * math.pi - diff
                        if diff < half_arc:
                            r.take_damage(SWORD_DAMAGE)
                            self._spawn_particles(r.x, r.y, (255, 255, 220), 6)
                            if not r.alive:
                                self._handle_robot_death(r)
                self._spawn_particles(
                    self.player.x + math.cos(self.player.angle) * 20,
                    self.player.y + math.sin(self.player.angle) * 20,
                    (220, 220, 255), 8)
        else:
            # === BẮN SÚNG ===
            if self.shoot_cd <= 0 and self.player.alive and not self.player.is_reloading:
                    # Infinite ammo - no clip check needed
                    gun_info = GUNS_DATA[self.selected_weapon]
                    self.shoot_cd = gun_info['fire_rate']
                    self.player.gun_flash_timer = 0.15  # Lóe sáng đầu nòng
                    self.player.trigger_shoot_anim()  # Animation bắn sprite
                    
                    # Bắn đạn
                    if self.selected_weapon == 'shotgun':
                        # Bắn 4 tia hình quạt lệch nhau
                        for offset in [-15, -5, 5, 15]:
                            rad = math.radians(offset)
                            self.bullets.append(Bullet(self.player.x, self.player.y, self.player.angle + rad, self.selected_weapon))
                    else:
                        self.bullets.append(Bullet(self.player.x, self.player.y, self.player.angle, self.selected_weapon))
                        
                    self._spawn_particles(self.player.x + math.cos(self.player.angle)*15,
                                        self.player.y + math.sin(self.player.angle)*15, ORANGE, 5)

    def _spawn_particles(self, x, y, color, count):
        for _ in range(count):
            self.particles.append(Particle(x, y, color, life=random.uniform(0.3, 0.8), size=random.randint(2, 5)))

    def _handle_robot_death(self, r):
        self.robots_killed += 1
        # Nhận từ 1 đến 3 linh kiện robot (cores)
        earned = random.randint(1, 3)
        self.coins += earned
        
        self._spawn_particles(r.x, r.y, r.color, 15)
        # Thả vật phẩm (mặc định 50%, nếu có Pet Lucky Cat thì tăng lên 75%)
        drop_rate = 0.75 if (hasattr(self.player, 'selected_pet') and self.player.selected_pet == 'lucky_cat') else 0.5
        if random.random() < drop_rate:
            weighted_types = ['battery', 'battery', 'battery', 'bulb', 'bulb', 'bulb',
                              'medkit', 'shoes', 'magnet', 'wave']
            itype = random.choice(weighted_types)
            self.level.items.append(Item(r.x, r.y, itype))

    def update(self):
        dt = 1.0 / FPS
        if self.state != 'playing':
            if self.shop_error_timer > 0:
                self.shop_error_timer -= dt
            return

        # Infinite ammo - không cần auto-reload

        if self.shoot_cd > 0: self.shoot_cd -= dt
        keys = pygame.key.get_pressed()
        mx, my = pygame.mouse.get_pos()
        mouse_buttons = pygame.mouse.get_pressed()

        # ---- NHÂN VẬT LUÔN XOAY THEO CON CHUỘT ----
        world_mx = mx + self.cam_x
        world_my = my + self.cam_y
        if self.player.alive:
            self.player.angle = math.atan2(world_my - self.player.y, world_mx - self.player.x)

        # ---- GIỮ CHUỘT TRÁI → BẮN LIÊN TỤC (mọi loại súng) ----
        if mouse_buttons[0] and self.player.weapon == 'gun' and self.shoot_cd <= 0 and self.player.alive and not self.player.is_reloading:
                # Infinite ammo - no clip check needed
                gun_info = GUNS_DATA[self.selected_weapon]
                self.shoot_cd = gun_info['fire_rate']
                self.player.gun_flash_timer = 0.15
                self.player.trigger_shoot_anim()
                if self.selected_weapon == 'shotgun':
                    for offset in [-15, -5, 5, 15]:
                        rad = math.radians(offset)
                        self.bullets.append(Bullet(self.player.x, self.player.y, self.player.angle + rad, self.selected_weapon))
                else:
                    self.bullets.append(Bullet(self.player.x, self.player.y, self.player.angle, self.selected_weapon))
                self._spawn_particles(self.player.x + math.cos(self.player.angle)*15,
                                      self.player.y + math.sin(self.player.angle)*15, ORANGE, 5)

        # Tự động spawn thêm vật phẩm ngẫu nhiên theo thời gian chơi
        self.item_spawn_timer -= dt
        if self.item_spawn_timer <= 0:
            self.item_spawn_timer = random.uniform(8.0, 15.0)  # Tầm 8 - 15 giây spawn 1 cái
            self._spawn_dynamic_item()

        # Đèn được bật/tắt bằng Space (toggle), không tốn năng lượng
        # light_on đã được toggle trong handle_events
        self.player.sprinting = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]

        ice = (self.level_num == 4)
        self.player.update(keys, mx, my, self.cam_x, self.cam_y, self.level.walls, dt, map_w=self.level.map_w, map_h=self.level.map_h, ice_level=ice)

        # ---- AUTO-PLAY (BFS / A*) - TURBO MODE ----
        if self.autoplay_mode and self.player.alive:
            pf_fn = pf_bfs if self.autoplay_mode == 'bfs' else pf_astar
            alive_robots = [r for r in self.level.robots if r.alive]
            if not alive_robots:
                self.autoplay_mode = None  # Tất cả robot chết → tắt chế độ
            elif pf_fn:
                # Chọn robot gần nhất
                target_r = min(alive_robots, key=lambda r: math.hypot(r.x - self.player.x, r.y - self.player.y))
                self.autoplay_timer -= dt
                if self.autoplay_timer <= 0 or not self.autoplay_path:
                    self.autoplay_path = pf_fn(
                        (self.player.x, self.player.y),
                        (target_r.x, target_r.y),
                        self.level.walls, self.level.map_w, self.level.map_h
                    )
                    self.autoplay_timer = 0.3  # Tính lại nhanh hơn (0.3s thay vì 0.8s)

                # Di chuyển theo waypoint - tốc độ nhanh gấp 2.5
                if self.autoplay_path:
                    wp_x, wp_y = self.autoplay_path[0]
                    move_angle = math.atan2(wp_y - self.player.y, wp_x - self.player.x)
                    spd = self.player.speed * 1.8  # Tốc độ vừa phải
                    dx = math.cos(move_angle) * spd
                    dy = math.sin(move_angle) * spd
                    walls_l = self.level.walls
                    import pygame as _pg
                    nx = self.player.x + dx
                    ny = self.player.y + dy
                    pr = self.player.radius
                    def hits_wall(px, py):
                        r = _pg.Rect(px - pr, py - pr, pr*2, pr*2)
                        return any(r.colliderect(w) for w in walls_l)
                    if not hits_wall(nx, self.player.y): self.player.x = nx
                    if not hits_wall(self.player.x, ny): self.player.y = ny
                    # Xóa waypoint đã đến gần (threshold nhỏ hơn = chính xác hơn)
                    if math.hypot(wp_x - self.player.x, wp_y - self.player.y) < 18:
                        self.autoplay_path.pop(0)

                # Tự động nhắm và bắn robot mục tiêu - tầm bắn xa hơn
                dist_target = math.hypot(target_r.x - self.player.x, target_r.y - self.player.y)
                angle_to_target = math.atan2(target_r.y - self.player.y, target_r.x - self.player.x)
                self.player.angle = angle_to_target
                if dist_target < 500 and self.player.weapon == 'gun':
                    self.trigger_attack()
        if not self.player.alive:

            self.state = 'gameover'
            self._save_progress()  # Lưu tiến trình khi chết để giữ lại số Cores đã cày cuốc
            return

        # Camera
        self.cam_x = self.player.x - WIDTH // 2
        self.cam_y = self.player.y - HEIGHT // 2
        if self.level.map_w < WIDTH:
            self.cam_x = (self.level.map_w - WIDTH) // 2
        else:
            self.cam_x = max(0, min(self.level.map_w - WIDTH, self.cam_x))
            
        if self.level.map_h < HEIGHT:
            self.cam_y = (self.level.map_h - HEIGHT) // 2
        else:
            self.cam_y = max(0, min(self.level.map_h - HEIGHT, self.cam_y))

        # Bullets
        for b in self.bullets: b.update(self.level.walls, dt, map_w=self.level.map_w, map_h=self.level.map_h)
        
        # Xử lý kích nổ cho đạn lựu đạn (Grenade) chết
        for b in self.bullets:
            if not b.alive and b.gun_type == 'grenade':
                expl_radius = 130
                expl_damage = GUNS_DATA['grenade']['damage']
                
                # Vẽ hiệu ứng sóng kích nổ đẹp mắt bằng hạt phát sáng
                self._spawn_particles(b.x, b.y, (255, 100, 0), 20)
                self._spawn_particles(b.x, b.y, YELLOW, 15)
                for _ in range(25):
                    ang = random.uniform(0, 2 * math.pi)
                    spd = random.uniform(2, 6)
                    self.particles.append(Particle(b.x, b.y, (255, 150, 50),
                                                   life=random.uniform(0.4, 0.8),
                                                   size=random.randint(4, 7),
                                                   vx=math.cos(ang)*spd, vy=math.sin(ang)*spd))
                
                # Gây sát thương diện rộng giảm dần theo khoảng cách
                for r in self.level.robots:
                    if not r.alive: continue
                    dist = math.hypot(r.x - b.x, r.y - b.y)
                    if dist < expl_radius:
                        factor = 1.0 - (dist / expl_radius)
                        dmg = int(expl_damage * factor)
                        r.take_damage(max(10, dmg))
                        if not r.alive:
                            self._handle_robot_death(r)
                            
        self.bullets = [b for b in self.bullets if b.alive]

        # Bullet-robot collision
        for b in self.bullets:
            if not b.alive: continue
            for r in self.level.robots:
                if not r.alive: continue
                if math.hypot(b.x - r.x, b.y - r.y) < b.radius + r.radius:
                    # Lấy sát thương của súng từ b.gun_type
                    gun_info = GUNS_DATA[b.gun_type]
                    
                    if b.gun_type == 'grenade':
                        # Lựu đạn chạm robot -> Kích nổ tức thì bằng cách cho chết
                        b.alive = False
                    else:
                        # Súng thông thường
                        r.take_damage(gun_info['damage'])
                        if b.gun_type != 'sniper':
                            b.alive = False
                        self._spawn_particles(r.x, r.y, r.color, 8)
                        if not r.alive:
                            self._handle_robot_death(r)
                    
                    if b.gun_type != 'sniper':
                        break

        # Khả năng đẩy lùi bằng sóng âm của Plasma Pup
        if getattr(self.player, 'pet_sonic_burst', False):
            self.player.pet_sonic_burst = False
            wave_range = 180
            # Hiệu ứng sóng âm lan tỏa màu hồng tím phát sáng cực chất!
            self._spawn_particles(self.player.x, self.player.y, (255, 100, 255), 20)
            for r in self.level.robots:
                if not r.alive: continue
                dist = math.hypot(r.x - self.player.x, r.y - self.player.y)
                if dist < wave_range:
                    ang = math.atan2(r.y - self.player.y, r.x - self.player.x)
                    push_dist = 65 * (1.0 - dist / wave_range)
                    r.x += math.cos(ang) * push_dist
                    r.y += math.sin(ang) * push_dist
                    r.take_damage(5) # Sóng âm gây sát thương nhẹ
                    if not r.alive:
                        self._handle_robot_death(r)

        # Robots
        for r in self.level.robots:
            if not r.alive: continue
            in_light = self._is_in_player_light(r.x, r.y)
            shot = r.update(self.player, self.level.walls, dt, in_light, map_w=self.level.map_w, map_h=self.level.map_h)
            if shot is not None:
                self.enemy_bullets.append(shot)

        # Cập nhật đạn robot (enemy bullets)
        for eb in self.enemy_bullets:
            eb.update(self.level.walls, dt, map_w=self.level.map_w, map_h=self.level.map_h)
        self.enemy_bullets = [eb for eb in self.enemy_bullets if eb.alive]

        # Kiểm tra đạn robot trúng người chơi
        for eb in self.enemy_bullets:
            if not eb.alive: continue
            dist = math.hypot(eb.x - self.player.x, eb.y - self.player.y)
            if dist < eb.radius + self.player.radius:
                self.player.take_damage(eb.enemy_dmg)
                eb.alive = False
                self._spawn_particles(self.player.x, self.player.y, (255, 80, 30), 8)
        self.enemy_bullets = [eb for eb in self.enemy_bullets if eb.alive]

        # Planted lights - dụ robot
        for pl in self.planted_lights:
            pl.update(dt)
            if pl.alive:
                for r in self.level.robots:
                    if r.alive and r.rtype == 'blue' and r.fear_light:
                        d = math.hypot(r.x - pl.x, r.y - pl.y)
                        if d < pl.radius and d > 0:
                            ang = math.atan2(pl.y - r.y, pl.x - r.x)
                            r.x += math.cos(ang) * r.speed * 0.8
                            r.y += math.sin(ang) * r.speed * 0.8
        self.planted_lights = [p for p in self.planted_lights if p.alive]

        # Items
        for item in self.level.items:
            if not item.alive: continue
            
            # Nếu đang có hiệu ứng nam châm, tự động hút vật phẩm về phía người chơi trong phạm vi 350px
            if self.magnet_timer > 0:
                dist = math.hypot(self.player.x - item.x, self.player.y - item.y)
                if dist < 350 and dist > 0:
                    ang = math.atan2(self.player.y - item.y, self.player.x - item.x)
                    # Hút với tốc độ tăng dần khi càng ở gần
                    pull_speed = 360 * dt
                    item.x += math.cos(ang) * pull_speed
                    item.y += math.sin(ang) * pull_speed

            item.update(dt)
            d = math.hypot(item.x - self.player.x, item.y - self.player.y)
            if d < self.player.radius + item.radius:
                result = item.apply(self.player)
                item.alive = False
                self._spawn_particles(item.x, item.y, item.color, 10)
                if result == 'magnet':
                    self.magnet_timer = 10.0
                elif result == 'wave':
                    for r in self.level.robots:
                        if r.alive:
                            d2 = math.hypot(r.x - self.player.x, r.y - self.player.y)
                            if d2 < 200 and d2 > 0:
                                ang = math.atan2(r.y - self.player.y, r.x - self.player.x)
                                r.x += math.cos(ang) * 80
                                r.y += math.sin(ang) * 80
                    self._spawn_particles(self.player.x, self.player.y, (50, 150, 255), 20)
        self.level.items = [i for i in self.level.items if i.alive]

        # Timers
        if self.scan_timer > 0: self.scan_timer -= dt
        else: self.scan_active = False
        if self.pulse_timer > 0: self.pulse_timer -= dt
        if self.magnet_timer > 0: self.magnet_timer -= dt

        # Particles
        for p in self.particles: p.update(dt)
        self.particles = [p for p in self.particles if p.alive]

        # Sandstorm (màn 3)
        if self.level_num == 2:
            self.sandstorm_offset += dt * 50

        # Kiểm tra hết robot -> qua màn
        alive_robots = sum(1 for r in self.level.robots if r.alive)
        if alive_robots == 0:
            # Mở khóa màn tiếp theo
            if self.level_num + 2 > self.levels_unlocked:
                self.levels_unlocked = min(6, self.level_num + 2)
            # Luôn lưu xu và tiến trình khi thắng màn
            self._save_progress()
            if self.level_num < 5:
                self.start_level(self.level_num + 1)
            else:
                self.state = 'victory'

    def _is_in_player_light(self, rx, ry):
        """Kiểm tra robot có nằm trong vùng sáng tam giác không"""
        if not self.player.light_on:
            return False
        dx = rx - self.player.x
        dy = ry - self.player.y
        dist = math.hypot(dx, dy)
        if dist > LIGHT_RANGE:
            return False
        angle_to = math.atan2(dy, dx)
        diff = abs(angle_to - self.player.angle)
        if diff > math.pi: diff = 2 * math.pi - diff
        return diff < math.radians(LIGHT_ANGLE / 2)

    def _is_visible(self, ox, oy):
        """Kiểm tra đối tượng có nhìn thấy được không (trong vùng sáng hoặc gần)"""
        d = math.hypot(ox - self.player.x, oy - self.player.y)
        if d < DARK_RADIUS: return True
        if self.player.light_on and self._is_in_player_light(ox, oy): return True
        if self.scan_active and d < SCAN_RADIUS: return True
        if self.pulse_timer > 0: return True
        for pl in self.planted_lights:
            if math.hypot(ox - pl.x, oy - pl.y) < pl.radius: return True
        for ax, ay, ar in self.level.ambient_lights:
            if math.hypot(ox - ax, oy - ay) < ar: return True
        return False

    def draw(self):
        if self.state == 'story':
            elapsed = pygame.time.get_ticks() - self.story_start_tick
            self.story_all_done = draw_story(screen, elapsed)
            return
        if self.state == 'menu': draw_menu(screen, self.menu_sel, self.player_skin, self.equipped_weapons); return
        if self.state == 'backpack':
            draw_menu(screen, self.menu_sel, self.player_skin, self.equipped_weapons)
            mx, my = pygame.mouse.get_pos()
            elapsed = pygame.time.get_ticks() - getattr(self, 'backpack_anim_ticks', 0)
            anim_t = min(1.0, elapsed / 200.0)
            draw_backpack_screen(screen, self.unlocked_weapons, self.equipped_weapons,
                                 self.unlocked_pets, self.selected_pet, self.coins, self.player_skin, (mx, my), anim_t)
            return
        if self.state == 'level_select': draw_level_select(screen, self.level_sel, self.levels_unlocked); return
        if self.state == 'controls': draw_controls_screen(screen); return
        if self.state == 'items':
            draw_shop_screen(screen, self.selected_weapon, self.unlocked_weapons, self.coins, self.preview_weapon, self.shop_error_timer,
                             self.unlocked_pets, self.selected_pet, self.shop_tab, self.preview_pet, self.player_skin)
            return
        if self.state == 'achievements': draw_achievements_screen(screen, self.robots_killed); return
        if self.state == 'intro': draw_intro_screen(screen); return

        # Game world rendering
        world_surf = pygame.Surface((WIDTH, HEIGHT))
        self.level.draw_bg(world_surf, self.cam_x, self.cam_y)
        self.level.draw_walls(world_surf, self.cam_x, self.cam_y)

        # Planted lights
        for pl in self.planted_lights:
            pl.draw(world_surf, self.cam_x, self.cam_y)

        # Items (chỉ vẽ nếu visible)
        for item in self.level.items:
            if item.alive and self._is_visible(item.x, item.y):
                item.draw(world_surf, self.cam_x, self.cam_y)

        # Robots (chỉ vẽ nếu visible)
        for r in self.level.robots:
            if r.alive and self._is_visible(r.x, r.y):
                r.draw(world_surf, self.cam_x, self.cam_y)

        # Bullets (người chơi + robot)
        for b in self.bullets:
            if b.alive: b.draw(world_surf, self.cam_x, self.cam_y)
        for eb in self.enemy_bullets:
            if eb.alive: eb.draw(world_surf, self.cam_x, self.cam_y)

        # Player
        self.player.draw(world_surf, self.cam_x, self.cam_y)

        # Particles
        for p in self.particles:
            p.draw(world_surf, self.cam_x, self.cam_y)

        # === LIGHTING OVERLAY ===
        light_mask = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        light_mask.fill((0, 0, 0, 220))  # Tối đen

        px = int(self.player.x - self.cam_x)
        py = int(self.player.y - self.cam_y)

        # Vùng gần CR7 luôn sáng (tròn nhỏ)
        pygame.draw.circle(light_mask, (0, 0, 0, 0), (px, py), DARK_RADIUS)

        # Đèn tam giác
        if self.player.light_on:
            self._draw_cone_light(light_mask, px, py, self.player.angle, LIGHT_RANGE, math.radians(LIGHT_ANGLE))

        # Planted lights
        for pl in self.planted_lights:
            plx = int(pl.x - self.cam_x)
            ply = int(pl.y - self.cam_y)
            frac = pl.timer / PLANTED_LIGHT_DURATION
            r = int(pl.radius * frac)
            if r > 5:
                pygame.draw.circle(light_mask, (0, 0, 0, 0), (plx, ply), r)

        # Ambient lights
        for ax, ay, ar in self.level.ambient_lights:
            alx = int(ax - self.cam_x)
            aly = int(ay - self.cam_y)
            if -ar < alx < WIDTH + ar and -ar < aly < HEIGHT + ar:
                pygame.draw.circle(light_mask, (0, 0, 0, 80), (alx, aly), ar)

        # Scan hiệu ứng
        if self.scan_active:
            pygame.draw.circle(light_mask, (0, 0, 0, 0), (px, py), int(SCAN_RADIUS * (1 - self.scan_timer/1.5) + 50))

        # Xung sáng
        if self.pulse_timer > 0:
            light_mask.fill((0, 0, 0, int(50 * self.pulse_timer / 0.5)))

        world_surf.blit(light_mask, (0, 0))

        # Sandstorm overlay (màn 3)
        if self.level_num == 2:
            sand = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            sand.fill((200, 180, 100, 40))
            for i in range(30):
                sx = (i * 97 + int(self.sandstorm_offset)) % WIDTH
                sy = (i * 53 + int(self.sandstorm_offset * 0.7)) % HEIGHT
                pygame.draw.line(sand, (180, 160, 80, 60), (sx, sy), (sx + 30, sy + 5), 1)
            world_surf.blit(sand, (0, 0))

        # Sương mù (màn 4)
        if self.level_num == 3:
            fog = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            t = pygame.time.get_ticks() / 1000
            fog.fill((150, 150, 160, 30))
            for i in range(10):
                fx = int((i * 200 + math.sin(t + i) * 50) % WIDTH)
                fy = int((i * 150 + math.cos(t * 0.7 + i) * 30) % HEIGHT)
                pygame.draw.circle(fog, (180, 180, 190, 20), (fx, fy), 80)
            world_surf.blit(fog, (0, 0))

        screen.blit(world_surf, (0, 0))
        # ----- Crosshair (pink) -----
        mx, my = pygame.mouse.get_pos()
        cross_color = (255, 105, 180)  # Pink
        size = 12
        # Horizontal line
        pygame.draw.line(screen, cross_color, (mx - size, my), (mx + size, my), 2)
        # Vertical line
        pygame.draw.line(screen, cross_color, (mx, my - size), (mx, my + size), 2)

        # HUD
        alive_r = sum(1 for r in self.level.robots if r.alive)
        draw_hud(screen, self.player, self.level_num, alive_r, self.player.light_on)

        # Bản đồ con (Minimap) ở góc dưới bên trái
        if self.state in ['playing', 'level_intro', 'paused']:
            draw_minimap(screen, self.player, self.level, self.bullets, self.cam_x, self.cam_y)

        if self.state == 'level_intro':
            elapsed_intro = pygame.time.get_ticks() - self.level_intro_start_tick
            draw_level_intro(screen, self.level_num, elapsed_intro)
        elif self.state == 'gameover':
            draw_game_over(screen, self.gameover_sel)
        elif self.state == 'victory':
            draw_victory(screen)
        elif self.state == 'paused':
            draw_pause_menu(screen, self.pause_sel)

    def _draw_cone_light(self, mask, cx, cy, angle, length, spread):
        """Vẽ vùng sáng hình tam giác (quạt nón) lên light mask"""
        steps = 30
        points = [(cx, cy)]
        for i in range(steps + 1):
            a = angle - spread / 2 + spread * i / steps
            lx = cx + int(math.cos(a) * length)
            ly = cy + int(math.sin(a) * length)
            points.append((lx, ly))
        if len(points) >= 3:
            pygame.draw.polygon(mask, (0, 0, 0, 0), points)
            # Viền sáng mờ
            glow_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            glow_points = [(cx, cy)]
            for i in range(steps + 1):
                a = angle - spread / 2 + spread * i / steps
                lx = cx + int(math.cos(a) * (length + 20))
                ly = cy + int(math.sin(a) * (length + 20))
                glow_points.append((lx, ly))
            if len(glow_points) >= 3:
                pygame.draw.polygon(glow_surf, (255, 255, 200, 15), glow_points)
            mask.blit(glow_surf, (0, 0))

    def _spawn_dynamic_item(self):
        """Tự động sinh ngẫu nhiên vật phẩm mới trên bản đồ khi đang chơi"""
        weighted_types = ['battery', 'battery', 'battery', 'bulb', 'bulb', 'bulb',
                          'medkit', 'shoes', 'magnet', 'wave']
        for _ in range(50):
            x = random.randint(60, self.level.map_w - 60)
            y = random.randint(60, self.level.map_h - 60)
            # Không spawn quá gần người chơi để tạo cảm giác tự nhiên
            if math.hypot(x - self.player.x, y - self.player.y) < 200:
                continue
            test = pygame.Rect(x - 10, y - 10, 20, 20)
            if not any(test.colliderect(w) for w in self.level.walls):
                itype = random.choice(weighted_types)
                self.level.items.append(Item(x, y, itype))
                # Hiệu ứng lấp lánh khi vật phẩm xuất hiện
                self._spawn_particles(x, y, (255, 255, 100), 5)
                break

    def buy_or_equip_previewed(self):
        if self.shop_tab == 'gun':
            wid = self.preview_weapon
            info = GUNS_DATA[wid]
            if wid in self.unlocked_weapons:
                self.play_accept_sound()
                # Đã sở hữu, trang bị súng này vào Slot 1 hoặc Slot 2
                if wid not in self.equipped_weapons:
                    if len(self.equipped_weapons) < 2:
                        self.equipped_weapons.append(wid)
                    else:
                        self.equipped_weapons[1] = wid
                self.selected_weapon = wid
                self.selected_gun = wid  # Đồng bộ
                self._save_progress()
                self._spawn_particles(875, 582, (100, 255, 120), 20)
            else:
                # Chưa sở hữu, tiến hành mua
                cost = info['price']
                if self.coins >= cost:
                    self.play_accept_sound()
                    self.coins -= cost
                    self.unlocked_weapons.append(wid)
                    # Tự động trang bị súng mới mua
                    if len(self.equipped_weapons) < 2:
                        self.equipped_weapons.append(wid)
                    else:
                        self.equipped_weapons[1] = wid
                    self.selected_weapon = wid
                    self.selected_gun = wid
                    self._save_progress()
                    self._spawn_particles(875, 582, (255, 215, 0), 25)
                else:
                    # Báo lỗi thiếu tiền
                    self.shop_error_timer = 1.5
                    self._spawn_particles(875, 582, (255, 50, 50), 15)
        elif self.shop_tab == 'pet':
            pid = self.preview_pet
            info = PETS_DATA[pid]
            if pid in self.unlocked_pets:
                self.play_accept_sound()
                # Đã sở hữu, trang bị hoặc hủy trang bị pet
                if self.selected_pet == pid:
                    self.selected_pet = None
                    self._spawn_particles(875, 582, (150, 150, 150), 15)
                else:
                    self.selected_pet = pid
                    self._spawn_particles(875, 582, (255, 100, 255), 20)
                self._save_progress()
            else:
                # Chưa sở hữu, tiến hành mua
                cost = info['price']
                if self.coins >= cost:
                    self.play_accept_sound()
                    self.coins -= cost
                    self.unlocked_pets.append(pid)
                    self.selected_pet = pid
                    self._save_progress()
                    self._spawn_particles(875, 582, (255, 215, 0), 25)
                else:
                    # Báo lỗi thiếu tiền
                    self.shop_error_timer = 1.5
                    self._spawn_particles(875, 582, (255, 50, 50), 15)

    def handle_backpack_click(self, mx, my):
        # Panel vẽ ở: x = WIDTH//2 - 450, y = HEIGHT//2 - 280, w = 900, h = 560
        px = WIDTH // 2 - 450
        py = HEIGHT // 2 - 280
        
        # 1. Click thẻ súng ở cột trái (X từ px+40 đến px+480)
        weapons_list = [w for w in ['pistol', 'shotgun', 'smg', 'sniper', 'advanced_sniper'] if w in self.unlocked_weapons]
        for idx, wid in enumerate(weapons_list):
            card_y = py + 115 + idx * 74
            card_rect = pygame.Rect(px + 40, card_y, 440, 66)
            if card_rect.collidepoint(mx, my):
                # Đã sở hữu, trang bị/hủy trang bị
                if wid in self.equipped_weapons:
                    # Chỉ cho phép hủy trang bị nếu còn ít nhất 1 súng
                    if len(self.equipped_weapons) > 1:
                        self.equipped_weapons.remove(wid)
                        if self.selected_weapon == wid:
                            self.selected_weapon = self.equipped_weapons[0]
                            self.selected_gun = self.selected_weapon
                        self._spawn_particles(mx, my, (255, 100, 50), 15)
                else:
                    # Chưa trang bị, tiến hành mang theo
                    if len(self.equipped_weapons) < 2:
                        self.equipped_weapons.append(wid)
                    else:
                        # Đầy 2 súng thì thay thế súng thứ hai
                        self.equipped_weapons[1] = wid
                    self.selected_weapon = wid
                    self.selected_gun = wid
                    self._spawn_particles(mx, my, (100, 255, 120), 20)
                return
                
        # 2. Click thẻ Pet ở cột phải (X từ px+500 đến px+860)
        pets_list = [p for p in ['mini_robot', 'plasma_pup', 'lucky_cat'] if p in self.unlocked_pets]
        for idx, pid in enumerate(pets_list):
            card_y = py + 115 + idx * 88
            card_rect = pygame.Rect(px + 500, card_y, 360, 78)
            if card_rect.collidepoint(mx, my):
                # Đã sở hữu, đồng hành/hủy đồng hành
                if self.selected_pet == pid:
                    self.selected_pet = None
                    self._spawn_particles(mx, my, (150, 150, 150), 12)
                else:
                    self.selected_pet = pid
                    self._spawn_particles(mx, my, (0, 255, 0), 18)
                return

        # 3. Nút đóng hành trang
        close_btn = pygame.Rect(WIDTH // 2 - 120, py + 490, 240, 42)
        if close_btn.collidepoint(mx, my):
            self.state = 'menu'
            self._save_progress()  # Chỉ lưu một lần duy nhất khi đóng hành trang
            self._spawn_particles(mx, my, (200, 200, 200), 10)

    def switch_active_gun(self, gun_id):
        """Hoán đổi súng đang sử dụng trong trận đấu và cập nhật thông số đạn"""
        if gun_id in self.unlocked_weapons:
            self.selected_weapon = gun_id
            if self.player:
                self.player.selected_gun = gun_id
                
                # Cập nhật thông số đạn theo súng mới
                gun_info = GUNS_DATA[gun_id]
                self.player.max_ammo_clip = gun_info['clip_size']
                self.player.ammo_clip = min(self.player.ammo_clip, gun_info['clip_size'])
                
                # Hủy nạp đạn của súng cũ
                self.player.is_reloading = False
                self.player.reload_timer = 0.0
                
                # Animation đổi súng mượt mà (xoay 180° + scale)
                self.player.weapon_switch_timer = 0.3
                
                # Tạo hiệu ứng hạt đổi súng
                self._spawn_particles(self.player.x, self.player.y, gun_info['color'], 8)

    def manage_music(self):
        if not self.music_loaded:
            return
        lobby_states = {'menu', 'level_select', 'items', 'controls', 'intro'}
        if self.state in lobby_states:
            if not pygame.mixer.music.get_busy():
                try:
                    pygame.mixer.music.play(-1)
                except Exception:
                    pass
        else:
            if pygame.mixer.music.get_busy():
                try:
                    pygame.mixer.music.stop()
                except Exception:
                    pass

# === MAIN LOOP ===
def main():
    game = Game()
    while True:
        game.handle_events()
        game.update()
        game.draw()
        game.manage_music()
        pygame.display.flip()
        clock.tick(FPS)

if __name__ == '__main__':
    main()

