"""Entities: Player, Robot, Bullet, Item, Particle, PlantedLight"""
import pygame, math, random, os
from constants import *
try:
    from pathfinder import dfs as pf_dfs
except ImportError:
    pf_dfs = None

# Cache font để tránh tạo lại mỗi frame (giảm lag)
_entity_font_cache = {}
def _get_font(size):
    if size not in _entity_font_cache:
        _entity_font_cache[size] = pygame.font.SysFont('segoeui', size)
    return _entity_font_cache[size]

class Player:
    # Cache sprite sheets tĩnh (chia sẻ giữa các instance)
    _sprites_loaded = False
    _walk_frames = {}   # {'down': [...], 'up': [...], 'right': [...], 'left': [...]}
    _shoot_frames = {}  # {'down': [...], 'up': [...], 'right': [...], 'left': [...]}
    _idle_frames = {}   # {'down': img, 'up': img, ...}
    SPRITE_SIZE = 48     # Kích thước mỗi frame sau khi scale

    @classmethod
    def _load_sprites(cls):
        """Load và cắt sprite sheet thành từng frame theo hướng"""
        if cls._sprites_loaded:
            return
        base = os.path.dirname(os.path.abspath(__file__))
        walk_path = os.path.join(base, "399fd479-c5e1-46da-9309-718522d56854.jpg")
        shoot_path = os.path.join(base, "soldier_shooting.png")

        def cut_sheet(path, cols, rows, bg_threshold=200):
            """Cắt sprite sheet thành list 2D [row][col], loại bỏ nền xám"""
            img = pygame.image.load(path).convert_alpha()
            w, h = img.get_width(), img.get_height()
            fw, fh = w // cols, h // rows
            frames = []
            for r in range(rows):
                row_frames = []
                for c in range(cols):
                    sub = img.subsurface(pygame.Rect(c * fw, r * fh, fw, fh)).copy()
                    # Loại bỏ nền xám/trắng nhạt bằng cách tạo surface RGBA mới
                    result = pygame.Surface((fw, fh), pygame.SRCALPHA)
                    for yi in range(fh):
                        for xi in range(fw):
                            color = sub.get_at((xi, yi))
                            if color[0] > bg_threshold and color[1] > bg_threshold and color[2] > bg_threshold:
                                continue  # Bỏ qua pixel nền
                            result.set_at((xi, yi), color)
                    # Scale về kích thước game
                    scaled = pygame.transform.smoothscale(result, (cls.SPRITE_SIZE, cls.SPRITE_SIZE))
                    row_frames.append(scaled)
                frames.append(row_frames)
            return frames

        try:
            # === WALK SPRITE SHEET (3 hàng x 8 cột) ===
            # Hàng 0: nhìn trước (down) - 4 frame idle + 4 frame đi (back view)
            # Hàng 1: nhìn sau (up) - 8 frame đi từ phía sau
            # Hàng 2: nhìn ngang (right) - 8 frame đi ngang
            wf = cut_sheet(walk_path, 8, 3)
            cls._walk_frames['down']  = wf[0][:4]   # 4 frame trước
            cls._walk_frames['up']    = wf[1][:4]    # 4 frame sau
            cls._walk_frames['right'] = wf[2][:4]    # 4 frame ngang phải
            # Lật ngang để tạo hướng trái
            cls._walk_frames['left'] = [pygame.transform.flip(f, True, False) for f in cls._walk_frames['right']]

            # Idle frames (frame đầu tiên mỗi hướng)
            cls._idle_frames['down']  = wf[0][0]
            cls._idle_frames['up']    = wf[1][0]
            cls._idle_frames['right'] = wf[2][0]
            cls._idle_frames['left']  = pygame.transform.flip(wf[2][0], True, False)

            # === SHOOT SPRITE SHEET (5 hàng x 6 cột) ===
            if os.path.exists(shoot_path):
                sf = cut_sheet(shoot_path, 6, 5)
                cls._shoot_frames['down']  = sf[0][:4]   # Bắn hướng trước
                cls._shoot_frames['right'] = sf[1][:4]    # Bắn hướng phải 
                cls._shoot_frames['up']    = sf[2][:4]    # Bắn hướng sau
                cls._shoot_frames['left']  = [pygame.transform.flip(f, True, False) for f in sf[3][:4]]
            else:
                cls._shoot_frames = cls._walk_frames.copy()

            cls._sprites_loaded = True
        except Exception as e:
            print(f"[WARN] Không load được sprite: {e}")
            cls._sprites_loaded = False

    def __init__(self, x, y):
        self.x, self.y = float(x), float(y)
        self.hp = PLAYER_HP
        self.max_hp = PLAYER_HP
        self.energy = PLAYER_ENERGY
        self.max_energy = PLAYER_ENERGY
        self.speed = PLAYER_SPEED
        self.radius = PLAYER_RADIUS
        self.light_on = False
        self.sprinting = False
        self.angle = 0  # hướng nhìn (rad)
        self.speed_boost_timer = 0
        self.invuln_timer = 0
        self.alive = True
        self.weapon = 'gun'  # 'sword' hoặc 'gun' - mặc định cầm súng lục
        self.sword_swing_timer = 0  # Animation chém kiếm (0 = không chém)
        self.gun_flash_timer = 0  # Animation lóe sáng đầu nòng khi bắn
        self.weapon_switch_timer = 0  # Animation đổi vũ khí (0.3s)
        # Hệ thống đạn dược
        self.ammo_clip = 10
        self.max_ammo_clip = 10
        self.ammo_reserve = 50
        self.max_ammo_reserve = 99
        self.is_reloading = False
        self.reload_timer = 0.0
        # Skin và màu áo đại diện các câu lạc bộ của CR7
        self.skin = 'mu'
        self.jersey_color = (200, 30, 30)
        self.number_color = (255, 255, 255)
        # === ANIMATION STATE ===
        self.anim_timer = 0.0        # Bộ đếm thời gian animation
        self.anim_frame = 0          # Frame hiện tại
        self.anim_speed = 0.12       # Giây/frame (tốc độ animation)
        self.facing = 'down'         # Hướng nhìn: 'up', 'down', 'left', 'right'
        self.is_moving = False       # Đang di chuyển?
        self.is_shooting_anim = False  # Đang trong animation bắn?
        self.shoot_anim_timer = 0.0  # Timer animation bắn
        # Load sprites
        Player._load_sprites()

    def set_skin(self, skin):
        self.skin = skin
        if skin == 'mu':
            self.jersey_color = (200, 30, 30)
            self.number_color = (255, 255, 255)
        elif skin == 'rm':
            self.jersey_color = (240, 240, 240)
            self.number_color = (30, 30, 30)
        elif skin == 'an':
            self.jersey_color = (255, 215, 0)
            self.number_color = (30, 30, 255)

    def update(self, keys, mx, my, cam_x, cam_y, walls, dt, map_w=MAP_W, map_h=MAP_H, ice_level=False):
        if not self.alive:
            return

        # Di chuyển
        dx, dy = 0, 0
        if keys[pygame.K_w]: dy -= 1
        if keys[pygame.K_s]: dy += 1
        if keys[pygame.K_a]: dx -= 1
        if keys[pygame.K_d]: dx += 1

        # Hướng nhìn theo phím di chuyển (không dùng chuột)
        if dx != 0 or dy != 0:
            self.angle = math.atan2(dy, dx)
            # Xác định hướng nhìn cho sprite animation
            if abs(dx) > abs(dy):
                self.facing = 'right' if dx > 0 else 'left'
            else:
                self.facing = 'down' if dy > 0 else 'up'
            self.is_moving = True
        else:
            self.is_moving = False

        if dx != 0 or dy != 0:
            ln = math.hypot(dx, dy)
            dx, dy = dx / ln, dy / ln

        spd = self.speed
        if self.speed_boost_timer > 0:
            spd *= 1.3
            self.speed_boost_timer -= dt
        if self.sprinting:
            spd *= PLAYER_SPRINT_MULT

        if ice_level:
            spd *= 1.4  # băng trơn tăng tốc

        dx *= spd
        dy *= spd

        # Va chạm tường
        nx = self.x + dx
        ny = self.y + dy
        pr = self.radius
        if not self._collide_walls(nx, self.y, pr, walls):
            self.x = nx
        if not self._collide_walls(self.x, ny, pr, walls):
            self.y = ny

        # Giới hạn trong map
        self.x = max(pr, min(map_w - pr, self.x))
        self.y = max(pr, min(map_h - pr, self.y))

        # Năng lượng: đèn không tốn năng lượng, chỉ hồi khi tắt đèn
        if not self.light_on:
            self.energy = min(self.max_energy, self.energy + LIGHT_REGEN * dt)

        if self.invuln_timer > 0:
            self.invuln_timer -= dt
        if self.sword_swing_timer > 0:
            self.sword_swing_timer -= dt
        if self.gun_flash_timer > 0:
            self.gun_flash_timer -= dt
        if self.weapon_switch_timer > 0:
            self.weapon_switch_timer -= dt
        if self.is_reloading:
            self.reload_timer -= dt
            if self.reload_timer <= 0:
                self.is_reloading = False
                self.reload_timer = 0
                # Tiến hành nạp đạn từ kho đạn dự trữ vào băng đạn
                need = self.max_ammo_clip - self.ammo_clip
                fill = min(need, self.ammo_reserve)
                self.ammo_clip += fill
                self.ammo_reserve -= fill

        # === CẬP NHẬT ANIMATION SPRITE ===
        if self.is_shooting_anim:
            self.shoot_anim_timer -= dt
            if self.shoot_anim_timer <= 0:
                self.is_shooting_anim = False
            self.anim_timer += dt
            if self.anim_timer >= 0.06:  # Animation bắn nhanh hơn
                self.anim_timer = 0
                self.anim_frame = (self.anim_frame + 1) % 4
        elif self.is_moving:
            self.anim_timer += dt
            if self.anim_timer >= self.anim_speed:
                self.anim_timer = 0
                self.anim_frame = (self.anim_frame + 1) % 4
        else:
            self.anim_frame = 0
            self.anim_timer = 0

        # Cập nhật các Kỹ năng bị động của Pet
        if hasattr(self, 'selected_pet') and self.selected_pet:
            self.pet_timer = getattr(self, 'pet_timer', 0.0) + dt
            
            if self.selected_pet == 'mini_robot':
                if self.pet_timer >= 5.0:
                    self.pet_timer = 0.0
                    self.energy = min(self.max_energy, self.energy + 5)
                    
            elif self.selected_pet == 'plasma_pup':
                if self.pet_timer >= 4.0:
                    self.pet_timer = 0.0
                    self.pet_sonic_burst = True  # Flag báo cho main.py thực hiện đẩy lùi robot

    def take_damage(self, dmg):
        if self.invuln_timer > 0:
            return
        self.hp -= dmg
        self.invuln_timer = 0.5
        if self.hp <= 0:
            self.hp = 0
            self.alive = False

    def _collide_walls(self, x, y, r, walls):
        rect = pygame.Rect(x - r, y - r, r * 2, r * 2)
        for w in walls:
            if rect.colliderect(w):
                return True
        return False

    def trigger_shoot_anim(self):
        """Gọi khi bắn để kích hoạt animation bắn"""
        self.is_shooting_anim = True
        self.shoot_anim_timer = 0.35  # 0.35 giây animation bắn
        self.anim_frame = 0
        self.anim_timer = 0

    def draw(self, surf, cam_x, cam_y):
        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y)
        r = self.radius
        half = self.SPRITE_SIZE // 2

        # === VẼ SPRITE SOLDIER ===
        if Player._sprites_loaded:
            # Chọn frame phù hợp
            if self.is_shooting_anim and self.facing in Player._shoot_frames:
                frames = Player._shoot_frames[self.facing]
                idx = min(self.anim_frame, len(frames) - 1)
                frame = frames[idx]
            elif self.is_moving and self.facing in Player._walk_frames:
                frames = Player._walk_frames[self.facing]
                idx = self.anim_frame % len(frames)
                frame = frames[idx]
            elif self.facing in Player._idle_frames:
                frame = Player._idle_frames[self.facing]
            else:
                frame = Player._idle_frames.get('down', None)

            if frame:
                # Nhấp nháy khi bất tử (bỏ qua 1 frame / 2)
                if self.invuln_timer > 0 and int(self.invuln_timer * 10) % 2 == 0:
                    # Tạo bản sao trắng nhấp nháy
                    flash_frame = frame.copy()
                    flash_frame.set_alpha(120)
                    surf.blit(flash_frame, (sx - half, sy - half))
                else:
                    surf.blit(frame, (sx - half, sy - half))

                # Hiệu ứng lóe lửa đầu nòng khi bắn (muzzle flash overlay)
                if self.gun_flash_timer > 0 and self.weapon == 'gun':
                    fp = self.gun_flash_timer / 0.15
                    # Tính vị trí đầu nòng theo hướng
                    if self.facing == 'right':
                        fx, fy = sx + half - 4, sy - 4
                    elif self.facing == 'left':
                        fx, fy = sx - half + 4, sy - 4
                    elif self.facing == 'up':
                        fx, fy = sx + 6, sy - half + 4
                    else:  # down
                        fx, fy = sx - 6, sy + half - 8
                    fl_size = int(14 * fp)
                    # Ngôi sao lửa
                    pts = []
                    for i in range(8):
                        ang = i * math.pi / 4 + (1 - fp) * 2
                        l = fl_size * (1.2 if i % 2 == 0 else 0.5)
                        pts.append((fx + math.cos(ang) * l, fy + math.sin(ang) * l))
                    if len(pts) > 2:
                        pygame.draw.polygon(surf, (255, 80, 0), pts)
                        pts_in = []
                        for i in range(8):
                            ang = i * math.pi / 4 + (1 - fp) * 2
                            l = fl_size * (0.6 if i % 2 == 0 else 0.25)
                            pts_in.append((fx + math.cos(ang) * l, fy + math.sin(ang) * l))
                        pygame.draw.polygon(surf, (255, 220, 50), pts_in)
                        pygame.draw.circle(surf, WHITE, (fx, fy), max(1, int(3 * fp)))

        else:
            # Fallback: vẽ thô nếu không load được sprite
            pygame.draw.circle(surf, self.jersey_color, (sx, sy), r)
            pygame.draw.circle(surf, (230, 180, 140), (sx, sy - r - 4), 7)

        # === VŨ KHÍ (vẽ súng hoặc kiếm trên sprite lính) ===
        if self.weapon == 'sword':
            self._draw_sword(surf, sx, sy, r)
        else:
            self._draw_gun(surf, sx, sy, r)

        # Nhấp nháy khi bất tử
        if self.invuln_timer > 0 and int(self.invuln_timer * 10) % 2 == 0:
            pygame.draw.circle(surf, (255, 255, 255, 128), (sx, sy), r + 3, 2)

        # Cảnh báo hết đạn & thanh tiến trình nạp đạn
        if self.is_reloading:
            bar_w = 40
            bar_h = 6
            bx = sx - bar_w // 2
            by = sy - r - 25
            # Nền thanh nạp đạn
            pygame.draw.rect(surf, (30, 30, 30), (bx, by, bar_w, bar_h), border_radius=2)
            # Tiến trình nạp đạn
            progress = (1.2 - self.reload_timer) / 1.2
            progress = max(0.0, min(1.0, progress))
            pw = int(bar_w * progress)
            pygame.draw.rect(surf, (0, 200, 255), (bx, by, pw, bar_h), border_radius=2)
            # Viền thanh nạp đạn
            pygame.draw.rect(surf, WHITE, (bx, by, bar_w, bar_h), 1, border_radius=2)
            # Chữ nạp đạn nhấp nháy
            f_reload = _get_font(11)
            t_reload = f_reload.render("NẠP ĐẠN...", True, (0, 200, 255))
            surf.blit(t_reload, (sx - t_reload.get_width() // 2, by - 12))
        # Infinite ammo - không cần cảnh báo hết đạn


        # === VẼ PET ĐỒNG HÀNH FLOATING BÊN CẠNH ===
        if hasattr(self, 'selected_pet') and self.selected_pet:
            # Pet bay lơ lửng phía sau bên trái người chơi một chút
            t = pygame.time.get_ticks()
            float_y = int(math.sin(t * 0.005) * 5) # Dao động lơ lửng hình sin cực mượt
            
            # Tính góc đối diện góc nhìn người chơi để bay phía sau
            pet_angle = self.angle + math.radians(135)
            pet_dist = r + 24
            pet_x = sx + int(math.cos(pet_angle) * pet_dist)
            pet_y = sy + int(math.sin(pet_angle) * pet_dist) + float_y
            
            if self.selected_pet == 'mini_robot':
                # Vẽ quả cầu xanh phát sáng
                pygame.draw.circle(surf, (0, 200, 255), (pet_x, pet_y), 8)
                pygame.draw.circle(surf, WHITE, (pet_x, pet_y), 3)
                pygame.draw.rect(surf, (0, 255, 200), (pet_x - 4, pet_y - 2, 8, 3), border_radius=1)
                # Vẽ quầng phát sáng mờ xung quanh
                glow_s = pygame.Surface((32, 32), pygame.SRCALPHA)
                pygame.draw.circle(glow_s, (0, 200, 255, 60), (16, 16), 14)
                surf.blit(glow_s, (pet_x - 16, pet_y - 16))
                
            elif self.selected_pet == 'plasma_pup':
                # Vẽ chú chó điện tử màu hồng/tím dễ thương
                pygame.draw.circle(surf, (255, 100, 255), (pet_x, pet_y), 7)
                pygame.draw.circle(surf, (255, 100, 255), (pet_x + 5, pet_y - 2), 5) # Đầu cún
                pygame.draw.rect(surf, (255, 100, 255), (pet_x - 4, pet_y, 8, 9), border_radius=2) # Thân
                pygame.draw.line(surf, WHITE, (pet_x - 2, pet_y + 9), (pet_x - 2, pet_y + 13), 2) # Chân
                pygame.draw.line(surf, WHITE, (pet_x + 2, pet_y + 9), (pet_x + 2, pet_y + 13), 2)
                
            elif self.selected_pet == 'lucky_cat':
                # Vẽ chú mèo thần tài màu vàng may mắn
                pygame.draw.circle(surf, (255, 215, 0), (pet_x, pet_y), 8)
                pygame.draw.polygon(surf, (255, 215, 0), [(pet_x - 6, pet_y - 6), (pet_x - 5, pet_y - 12), (pet_x - 2, pet_y - 7)]) # Tai
                pygame.draw.polygon(surf, (255, 215, 0), [(pet_x + 6, pet_y - 6), (pet_x + 5, pet_y - 12), (pet_x + 2, pet_y - 7)])
                pygame.draw.circle(surf, WHITE, (pet_x, pet_y), 4) # Bụng
                pygame.draw.circle(surf, RED, (pet_x, pet_y + 7), 3) # Vòng cổ đỏ

    def _draw_sword(self, surf, sx, sy, r):
        """Vẽ thanh kiếm thẳng kiểu Fantasy - báng có pommel tam giác, ngọc tròn phát sáng ở hộ thủ, lưỡi kiếm thẳng chia hai tông màu và vệt chém hình trăng khuyết cực đẹp"""
        # Tính góc swing và hiệu ứng vung kiếm khi rút vũ khí
        scale = 1.0
        if hasattr(self, 'weapon_switch_timer') and self.weapon_switch_timer > 0:
            prog = self.weapon_switch_timer / 0.3
            scale = 1.0 - prog
            # Xoay kiếm cực ngầu 360 độ từ sau lưng ra tay
            sa = self.angle + math.radians(360) * prog
        elif self.sword_swing_timer > 0:
            prog = self.sword_swing_timer / SWORD_COOLDOWN
            swing_off = math.radians(SWORD_ARC) * (prog - 0.5)
            sa = self.angle + swing_off
        else:
            sa = self.angle

        scale = max(0.05, scale)
        perp = sa + math.pi / 2
        # Gốc tay cầm
        ox = sx + int(math.cos(self.angle) * (r - 2))
        oy = sy + int(math.sin(self.angle) * (r - 2))

        # --- 1. POMMEL (Đuôi kiếm hình tam giác) ---
        px0 = (ox - int(math.cos(sa) * (3 * scale)), oy - int(math.sin(sa) * (3 * scale)))  # Đỉnh tam giác hướng xuống dưới
        px1 = (ox + int(math.cos(perp) * (3 * scale)), oy + int(math.sin(perp) * (3 * scale)))
        px2 = (ox - int(math.cos(perp) * (3 * scale)), oy - int(math.sin(perp) * (3 * scale)))
        pygame.draw.polygon(surf, (150, 150, 155), [px0, px1, px2])
        pygame.draw.polygon(surf, (40, 40, 42), [px0, px1, px2], 1)

        # --- 2. GRIP (Chuôi sẫm màu) ---
        gl = int(11 * scale)  # Chiều dài chuôi
        gex = ox + int(math.cos(sa) * gl)
        gey = oy + int(math.sin(sa) * gl)
        pygame.draw.line(surf, (70, 70, 75), (ox, oy), (gex, gey), max(1, int(5 * scale)))
        pygame.draw.line(surf, (40, 40, 42), (ox, oy), (gex, gey), 1)

        # --- 3. CROSSGUARD (Thanh hộ thủ ngang vát góc) ---
        cg_w = int(11 * scale)  # Độ dài hộ thủ
        cg_t = max(1, int(3 * scale))   # Độ dày hộ thủ
        cgp1 = (gex + int(math.cos(perp) * cg_w), gey + int(math.sin(perp) * cg_w))
        cgp2 = (gex + int(math.cos(perp) * (cg_w - 2)) + int(math.cos(sa) * cg_t), gey + int(math.sin(perp) * (cg_w - 2)) + int(math.sin(sa) * cg_t))
        cgp3 = (gex - int(math.cos(perp) * (cg_w - 2)) + int(math.cos(sa) * cg_t), gey - int(math.sin(perp) * (cg_w - 2)) + int(math.sin(sa) * cg_t))
        cgp4 = (gex - int(math.cos(perp) * cg_w), gey - int(math.sin(perp) * cg_w))
        pygame.draw.polygon(surf, (90, 90, 95), [cgp1, cgp2, cgp3, cgp4])
        pygame.draw.polygon(surf, (40, 40, 42), [cgp1, cgp2, cgp3, cgp4], 1)

        # --- 4. GEM (Viên ngọc phát sáng ở trung tâm hộ thủ) ---
        gem_color = (255, 255, 255)
        if self.sword_swing_timer > 0:
            # Phát quang xanh tuyết cực mạnh khi chém
            glow_r = int(6 + 4 * (self.sword_swing_timer / SWORD_COOLDOWN))
            pygame.draw.circle(surf, (150, 230, 255, 120), (gex, gey), glow_r)
        pygame.draw.circle(surf, gem_color, (gex, gey), max(1.0, 3.5 * scale))
        pygame.draw.circle(surf, (40, 40, 42), (gex, gey), max(1.0, 3.5 * scale), 1)

        # --- 5. BLADE (Lưỡi kiếm thẳng chia hai tông màu) ---
        bl = int((SWORD_RANGE - 13) * scale)
        bsx = gex + int(math.cos(sa) * 2)
        bsy = gey + int(math.sin(sa) * 2)
        tx = bsx + int(math.cos(sa) * bl)
        ty = bsy + int(math.sin(sa) * bl)

        bw = max(1.0, 3.5 * scale)  # Chiều rộng lưỡi
        # Cạnh trái lưỡi
        b_left_base = (bsx + int(math.cos(perp) * bw), bsy + int(math.sin(perp) * bw))
        b_left_tip = (tx - int(math.cos(sa) * max(1, int(4 * scale))) + int(math.cos(perp) * bw), ty - int(math.sin(sa) * max(1, int(4 * scale))) + int(math.sin(perp) * bw))
        # Cạnh phải lưỡi
        b_right_base = (bsx - int(math.cos(perp) * bw), bsy - int(math.sin(perp) * bw))
        b_right_tip = (tx - int(math.cos(sa) * max(1, int(4 * scale))) - int(math.cos(perp) * bw), ty - int(math.sin(sa) * max(1, int(4 * scale))) - int(math.sin(perp) * bw))

        # Vẽ nửa sáng (màu bạc sáng)
        pygame.draw.polygon(surf, (225, 225, 230), [(bsx, bsy), b_left_base, b_left_tip, (tx, ty)])
        # Vẽ nửa tối (màu thép xám)
        pygame.draw.polygon(surf, (175, 175, 180), [(bsx, bsy), b_right_base, b_right_tip, (tx, ty)])

        # Vẽ viền đen sắc nét & gờ dọc trung tâm
        pygame.draw.polygon(surf, (40, 40, 42), [b_left_base, b_left_tip, (tx, ty), b_right_tip, b_right_base], 1)
        pygame.draw.line(surf, (40, 40, 42), (bsx, bsy), (tx, ty), 1)

        # --- 6. HÀO QUANG KHI VUNG KIẾM (Energy streaks) ---
        if self.sword_swing_timer > 0:
            glow_alpha = int(220 * (self.sword_swing_timer / SWORD_COOLDOWN))
            g_color = (200, 245, 255, glow_alpha)
            # Hai tia hào quang bám dọc lưỡi kiếm
            pygame.draw.line(surf, g_color, b_left_base, b_left_tip, 2)
            pygame.draw.line(surf, g_color, b_right_base, b_right_tip, 2)
            # Tia sáng ở mũi kiếm nhọn kéo dài ra trước
            pygame.draw.line(surf, (255, 255, 255, glow_alpha), (bsx, bsy), (tx + int(math.cos(sa)*5), ty + int(math.sin(sa)*5)), 2)

        # --- 7. HIỆU ỨNG VỆT CHÉM HÌNH TRĂNG KHUYẾT (Slash Arc) ---
        if self.sword_swing_timer > 0:
            ap = 1.0 - (self.sword_swing_timer / SWORD_COOLDOWN)  # tiến trình từ 0 -> 1
            ar = int(SWORD_RANGE * 1.1)
            
            slash = pygame.Surface((ar * 2 + 20, ar * 2 + 20), pygame.SRCALPHA)
            cx, cy = ar + 10, ar + 10
            
            ha = math.radians(SWORD_ARC / 2)
            s_a = self.angle - ha
            e_a = self.angle + ha
            
            # Vẽ hình cung bán nguyệt mịn màng
            trail_pts = []
            steps = 22
            for j in range(steps):
                # Tạo dải điểm quá khứ (trail) giảm dần bán kính và độ dày
                hist_ap = max(0.0, ap - j * (0.4 / steps))
                hist_a = s_a + (e_a - s_a) * hist_ap
                
                r_out = ar - j * 0.25
                r_in = ar - 11 + j * 0.35
                
                pt_out = (cx + math.cos(hist_a) * r_out, cy + math.sin(hist_a) * r_out)
                pt_in = (cx + math.cos(hist_a) * r_in, cy + math.sin(hist_a) * r_in)
                
                trail_pts.insert(0, pt_out)
                trail_pts.append(pt_in)
            
            if len(trail_pts) > 4:
                # Đổ màu bán nguyệt màu trắng xanh tuyết, trong suốt nhạt dần ở đuôi vệt chém
                alpha = int(190 * (1.0 - ap))
                pygame.draw.polygon(slash, (215, 240, 255, alpha), trail_pts)
                
                # Vẽ viền hào quang phát sáng ở mép ngoài cùng của vệt chém
                half_len = len(trail_pts) // 2
                for j in range(half_len - 1):
                    p1 = trail_pts[half_len - 1 - j]
                    p2 = trail_pts[half_len - 2 - j]
                    p_alpha = max(0, int(255 * (1.0 - ap) - j * (200 / half_len)))
                    pygame.draw.line(slash, (255, 255, 255, p_alpha), p1, p2, 2)
                    
            surf.blit(slash, (sx - ar - 10, sy - ar - 10))

    def _draw_gun(self, surf, sx, sy, r):
        """Vẽ súng thật vừa vặn trên tay lính, có animation đổi súng mượt mà"""
        scale = 1.0
        a = self.angle
        if hasattr(self, 'weapon_switch_timer') and self.weapon_switch_timer > 0:
            prog = self.weapon_switch_timer / 0.3
            scale = 1.0 - prog
            # Animation đổi súng: xoay 180° + scale nhỏ → lớn (tự nhiên hơn)
            a = self.angle + math.radians(180) * prog
        elif self.gun_flash_timer > 0:
            # Giật lùi khi bắn (recoil) - nhẹ hơn
            recoil_prog = self.gun_flash_timer / 0.15
            recoil_angle = math.radians(12) * recoil_prog
            if math.cos(self.angle) > 0:
                a -= recoil_angle
            else:
                a += recoil_angle

        # ----------------- VẼ SÚNG THẬT BẰNG HÌNH ẢNH -----------------
        wid = getattr(self, 'selected_gun', 'pistol')
        img_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"{wid}.png")
        if os.path.exists(img_path):
            try:
                if not hasattr(self, '_gun_images_cache'):
                    self._gun_images_cache = {}
                if wid not in self._gun_images_cache:
                    g_img = pygame.image.load(img_path).convert_alpha()
                    # Kích thước vừa vặn với lính 48px, giữ đúng tỉ lệ ảnh gốc
                    # pistol(100x70) shotgun(776x238) smg(405x180) sniper(366x157) adv(832x195)
                    gun_scales = {
                        'pistol': (16, 11),       # nhỏ gọn - súng lục
                        'shotgun': (30, 9),        # dài ngang - shotgun
                        'smg': (26, 12),           # trung bình - tiểu liên
                        'sniper': (32, 14),        # dài vừa - súng tỉa
                        'advanced_sniper': (36, 8) # rất dài mỏng - tỉa nâng cấp
                    }
                    size = gun_scales.get(wid, (24, 12))
                    self._gun_images_cache[wid] = pygame.transform.smoothscale(g_img, size)
                
                base_img = self._gun_images_cache[wid]
                
                # Áp dụng scale khi đổi súng
                if scale < 1.0:
                    sw = max(1, int(base_img.get_width() * scale))
                    sh = max(1, int(base_img.get_height() * scale))
                    base_img = pygame.transform.smoothscale(base_img, (sw, sh))
                
                # Lật ảnh khi hướng trái
                if math.cos(a) < 0:
                    base_img = pygame.transform.flip(base_img, False, True)
                
                rot_img = pygame.transform.rotate(base_img, -math.degrees(a))
                
                # Vị trí tay cầm súng (sát mép body lính)
                ox = sx + int(math.cos(a) * (r + 2))
                oy = sy + int(math.sin(a) * (r + 2))
                
                # Offset tâm súng = nửa chiều dài súng (để báng nằm ở tay, nòng hướng ra)
                gun_offsets = {
                    'pistol': 6,              # súng ngắn → offset nhỏ
                    'shotgun': 12,             # súng dài → offset lớn
                    'smg': 10,                 # trung bình
                    'sniper': 13,              # dài
                    'advanced_sniper': 15      # rất dài
                }
                center_dist = gun_offsets.get(wid, 10)
                cx = ox + int(math.cos(a) * center_dist)
                cy = oy + int(math.sin(a) * center_dist)
                
                rect = rot_img.get_rect(center=(cx, cy))
                surf.blit(rot_img, rect.topleft)
                
                # Hiệu ứng nổ lửa đầu nòng khi bắn
                if self.gun_flash_timer > 0:
                    fp = self.gun_flash_timer / 0.15
                    # Chiều dài nòng = offset tâm + nửa chiều dài ảnh súng
                    barrel_lens = {
                        'pistol': 14,          # nòng ngắn
                        'shotgun': 24,          # nòng dài
                        'smg': 20,             # nòng trung
                        'sniper': 26,           # nòng dài
                        'advanced_sniper': 30   # nòng rất dài
                    }
                    brl_l = barrel_lens.get(wid, 20)
                    flash_cx = ox + int(math.cos(a) * brl_l)
                    flash_cy = oy + int(math.sin(a) * brl_l)
                    fl_size = 10 * fp  # Lửa vừa phải
                    
                    # Ngôi sao lửa cam-vàng
                    pts_red = []
                    pts_yellow = []
                    for i in range(8):
                        ang = a + i * math.pi / 4 + (1 - fp) * 2
                        l_red = fl_size * (1.2 if i % 2 == 0 else 0.5)
                        l_yel = fl_size * (0.6 if i % 2 == 0 else 0.25)
                        pts_red.append((flash_cx + math.cos(ang)*l_red, flash_cy + math.sin(ang)*l_red))
                        pts_yellow.append((flash_cx + math.cos(ang)*l_yel, flash_cy + math.sin(ang)*l_yel))
                        
                    if len(pts_red) > 2:
                        pygame.draw.polygon(surf, (255, 60, 0), pts_red)
                        pygame.draw.polygon(surf, (255, 200, 0), pts_yellow)
                        pygame.draw.circle(surf, WHITE, (flash_cx, flash_cy), max(1, int(3 * fp)))
                return
            except Exception:
                pass
        # -------------------------------------------------------------

        scale = max(0.05, scale)
        perp = a + math.pi / 2
        # Gốc súng (nơi tay cầm)
        ox = sx + int(math.cos(a) * (r + 1))
        oy = sy + int(math.sin(a) * (r + 1))
        ca, sa_v = math.cos(a), math.sin(a)
        cp, sp = math.cos(perp), math.sin(perp)

        # === 1. BÁNG SÚNG GỖ CAM (Stock) - hình tam giác phía sau ===
        stk_l = int(14 * scale)  # chiều dài báng
        stk_w = max(1.0, 5 * scale)   # độ dày báng
        # Điểm gốc báng (phía sau lưng)
        s0 = (ox - int(ca * stk_l), oy - int(sa_v * stk_l))
        # 2 góc trên/dưới của báng (hình thang)
        s1 = (s0[0] + int(cp * stk_w), s0[1] + int(sp * stk_w))
        s2 = (s0[0] - int(cp * (stk_w - 1)), s0[1] - int(sp * (stk_w - 1)))
        # 2 góc phía trước (nối vào thân)
        s3 = (ox - int(cp * max(1.0, 2 * scale)), oy - int(sp * max(1.0, 2 * scale)))
        s4 = (ox + int(cp * max(1.0, 3 * scale)), oy + int(sp * max(1.0, 3 * scale)))
        stock_pts = [s1, s4, s3, s2]
        pygame.draw.polygon(surf, (220, 140, 30), stock_pts)    # Gỗ cam
        pygame.draw.polygon(surf, (180, 110, 20), stock_pts, 1) # Viền tối
        # Vân gỗ
        for i in range(3):
            t = 0.2 + i * 0.3
            vx = int(s1[0] + (s4[0] - s1[0]) * t)
            vy = int(s1[1] + (s4[1] - s1[1]) * t)
            vx2 = int(s2[0] + (s3[0] - s2[0]) * t)
            vy2 = int(s2[1] + (s3[1] - s2[1]) * t)
            pygame.draw.line(surf, (200, 120, 15), (vx, vy), (vx2, vy2), 1)

        # === 2. TAY CẦM (Grip/Pistol Grip) - nghiêng xuống ===
        grip_a = a + math.pi * 0.6
        gl = int(9 * scale)
        gex = ox + int(math.cos(grip_a) * gl)
        gey = oy + int(math.sin(grip_a) * gl)
        pygame.draw.line(surf, (200, 125, 25), (ox, oy), (gex, gey), max(1, int(4 * scale)))
        pygame.draw.line(surf, (170, 100, 15), (ox, oy), (gex, gey), max(1, int(2 * scale)))
        # Đế tay cầm
        pygame.draw.circle(surf, (190, 115, 20), (gex, gey), max(1.0, 2 * scale))

        # === 3. THÂN SÚNG / RECEIVER (hộp cơ - đen) ===
        rcv_l = int(14 * scale)
        rcv_w = max(1.0, 3 * scale)
        r0 = (ox - int(cp * rcv_w), oy - int(sp * rcv_w))
        r1 = (ox + int(cp * rcv_w), oy + int(sp * rcv_w))
        r2x = ox + int(ca * rcv_l)
        r2y = oy + int(sa_v * rcv_l)
        r2 = (r2x + int(cp * (rcv_w - 1)), r2y + int(sp * (rcv_w - 1)))
        r3 = (r2x - int(cp * (rcv_w - 1)), r2y - int(sp * (rcv_w - 1)))
        pygame.draw.polygon(surf, (45, 45, 50), [r0, r3, r2, r1])
        pygame.draw.polygon(surf, (70, 70, 78), [r0, r3, r2, r1], 1)

        # === 4. NÒNG SÚNG DÀI (Barrel) ===
        brl_s = (r2x, r2y)
        brl_l = int(16 * scale)
        brl_ex = r2x + int(ca * brl_l)
        brl_ey = r2y + int(sa_v * brl_l)
        pygame.draw.line(surf, (50, 50, 55), brl_s, (brl_ex, brl_ey), max(1, int(4 * scale)))
        pygame.draw.line(surf, (75, 75, 82), brl_s, (brl_ex, brl_ey), max(1, int(2 * scale)))
        # Lỗ nòng
        pygame.draw.circle(surf, (20, 20, 25), (brl_ex, brl_ey), max(1.0, 2 * scale))
        # Đầu nòng (muzzle brake)
        mb1 = (brl_ex + int(cp * max(1, int(3 * scale))), brl_ey + int(sp * max(1, int(3 * scale))))
        mb2 = (brl_ex - int(cp * max(1, int(3 * scale))), brl_ey - int(sp * max(1, int(3 * scale))))
        pygame.draw.line(surf, (60, 60, 68), mb1, mb2, max(1, int(2 * scale)))

        # === 5. ỐNG NGẮM (Scope) - trên thân súng ===
        sc_off = -int(cp * (rcv_w + max(1, int(3 * scale))))  # offset lên trên
        sc_offy = -int(sp * (rcv_w + max(1, int(3 * scale))))
        sc_sx = ox + int(ca * max(1, int(3 * scale))) + sc_off
        sc_sy = oy + int(sa_v * max(1, int(3 * scale))) + sc_offy
        sc_len = int(14 * scale)
        sc_ex = sc_sx + int(ca * sc_len)
        sc_ey = sc_sy + int(sa_v * sc_len)
        # Thân ống ngắm (hình trụ)
        pygame.draw.line(surf, (35, 35, 40), (sc_sx, sc_sy), (sc_ex, sc_ey), max(1, int(5 * scale)))
        pygame.draw.line(surf, (55, 55, 62), (sc_sx, sc_sy), (sc_ex, sc_ey), max(1, int(3 * scale)))
        # Thấu kính trước (đường kính lớn hơn)
        lens_f = (sc_ex + int(ca * max(1, int(1 * scale))), sc_ey + int(sa_v * max(1, int(1 * scale))))
        pygame.draw.circle(surf, (30, 30, 35), lens_f, max(1.0, 4 * scale))
        pygame.draw.circle(surf, (60, 80, 120), lens_f, max(1.0, 3 * scale))  # kính xanh
        pygame.draw.circle(surf, (100, 140, 200), lens_f, max(1.0, 1 * scale)) # phản chiếu
        # Thấu kính sau (đường kính nhỏ)
        lens_b = (sc_sx - int(ca * max(1, int(1 * scale))), sc_sy - int(sa_v * max(1, int(1 * scale))))
        pygame.draw.circle(surf, (30, 30, 35), lens_b, max(1.0, 3 * scale))
        pygame.draw.circle(surf, (50, 65, 100), lens_b, max(1.0, 2 * scale))
        # Chân đỡ ống ngắm (mount)
        mt1 = (sc_sx + int(ca * 2), sc_sy + int(sa_v * 2))
        mt1b = (mt1[0] - sc_off, mt1[1] - sc_offy)
        pygame.draw.line(surf, (60, 60, 65), mt1, mt1b, 2)
        mt2 = (sc_sx + int(ca * 10), sc_sy + int(sa_v * 10))
        mt2b = (mt2[0] - sc_off, mt2[1] - sc_offy)
        pygame.draw.line(surf, (60, 60, 65), mt2, mt2b, 2)

        # === 6. CÒ SÚNG + VONG CÒ (Trigger Guard) ===
        tg = (ox + int(ca * 5), oy + int(sa_v * 5))
        tg_d = (tg[0] + int(cp * 6), tg[1] + int(sp * 6))
        tg_b = (tg[0] + int(ca * 3) + int(cp * 5), tg[1] + int(sa_v * 3) + int(sp * 5))
        pygame.draw.line(surf, (55, 55, 60), tg, tg_d, 1)   # cò
        pygame.draw.line(surf, (55, 55, 60), tg_d, tg_b, 1) # vong cò

        # === 7. LÓE SÁNG ĐẦU NÒNG (Muzzle Flash) & VỎ ĐẠN ===
        if self.gun_flash_timer > 0:
            fp = self.gun_flash_timer / 0.15  # 1.0 -> 0.0
            
            # --- TÓE LỬA (Muzzle Flash) ---
            # Vẽ hình ngôi sao đa giác để tạo hiệu ứng nổ mạnh mẽ, không dùng Surface trong suốt nữa
            flash_cx = brl_ex + int(ca * 4)
            flash_cy = brl_ey + int(sa_v * 4)
            fl_size = 18 * fp  # Kích thước vệt lửa
            
            pts_red = []
            pts_yellow = []
            for i in range(8):
                ang = a + i * math.pi / 4 + (1 - fp) * 2
                # Cánh dài ngắn xen kẽ
                l_red = fl_size * (1.2 if i % 2 == 0 else 0.5)
                l_yel = fl_size * (0.7 if i % 2 == 0 else 0.3)
                pts_red.append((flash_cx + math.cos(ang)*l_red, flash_cy + math.sin(ang)*l_red))
                pts_yellow.append((flash_cx + math.cos(ang)*l_yel, flash_cy + math.sin(ang)*l_yel))
                
            if len(pts_red) > 2:
                pygame.draw.polygon(surf, (255, 60, 0), pts_red)      # Lớp đỏ cam ngoài
                pygame.draw.polygon(surf, (255, 200, 0), pts_yellow)  # Lớp vàng trong
                pygame.draw.circle(surf, (255, 255, 255), (flash_cx, flash_cy), int(4 * fp)) # Nhân trắng

            # --- VỎ ĐẠN VĂNG RA (Shell Ejection) ---
            # Vỏ đạn bay lên trên và ra sau
            fly_dist = (1.0 - fp) * 25
            shell_x = ox + int(ca * 5) - int(cp * fly_dist)  # Bay vuông góc lên
            shell_y = oy + int(sa_v * 5) - int(sp * fly_dist)
            
            # Quỹ đạo vòng cung (parabol nhẹ)
            shell_x -= int(ca * (1.0 - fp) * 15)
            shell_y -= int(sa_v * (1.0 - fp) * 15)
            
            # Xoay vỏ đạn liên tục
            shell_ang = (1.0 - fp) * math.pi * 4
            scx, scy = shell_x, shell_y
            slen = 6
            swid = 3
            # Tính 4 góc của vỏ đạn xoay
            s_ca, s_sa = math.cos(shell_ang), math.sin(shell_ang)
            s_cp, s_sp = math.cos(shell_ang + math.pi/2), math.sin(shell_ang + math.pi/2)
            
            sp1 = (scx + s_ca * slen/2 + s_cp * swid/2, scy + s_sa * slen/2 + s_sp * swid/2)
            sp2 = (scx - s_ca * slen/2 + s_cp * swid/2, scy - s_sa * slen/2 + s_sp * swid/2)
            sp3 = (scx - s_ca * slen/2 - s_cp * swid/2, scy - s_sa * slen/2 - s_sp * swid/2)
            sp4 = (scx + s_ca * slen/2 - s_cp * swid/2, scy + s_sa * slen/2 - s_sp * swid/2)
            
            pygame.draw.polygon(surf, (255, 200, 50), [sp1, sp2, sp3, sp4])
            pygame.draw.polygon(surf, (200, 150, 20), [sp1, sp2, sp3, sp4], 1)


class Robot:
    # Cache sprite sheets cho robot xanh trời (chia sẻ giữa các instance)
    _blue_sprites_loaded = False
    _blue_walk_frames = {}   # {'down': [...], 'up': [...], 'right': [...], 'left': [...]}
    _blue_idle_frames = {}   # {'down': img, 'up': img, ...}
    BLUE_SPRITE_SIZE = 48    # Kích thước mỗi frame sau khi scale

    # Cache sprite sheets cho robot xanh lá (lính bắn súng)
    _green_sprites_loaded = False
    _green_walk_frames = {}
    _green_idle_frames = {}
    GREEN_SPRITE_SIZE = 60

    # Cache cho khổng lồ xanh (white_giant) sử dụng chung ảnh quái xanh nhưng tỉ lệ lớn hơn
    _giant_sprites_loaded = False
    _giant_walk_frames = {}
    _giant_idle_frames = {}
    GIANT_SPRITE_SIZE = 110

    # Cache sprite sheets cho robot vàng (lính bắn súng mạnh)
    _yellow_sprites_loaded = False
    _yellow_walk_frames = {}
    _yellow_idle_frames = {}
    YELLOW_SPRITE_SIZE = 62

    @classmethod
    def _load_yellow_sprites(cls):
        """Load sprite sheet robot vàng từ 'robotvang.png' bằng thuật toán dò biên tự động cực kỳ chính xác"""
        if cls._yellow_sprites_loaded:
            return
        base = os.path.dirname(os.path.abspath(__file__))
        sprite_path = os.path.join(base, "robotvang.png")
        try:
            img = pygame.image.load(sprite_path).convert_alpha()
            w, h = img.get_width(), img.get_height()
            rows = 4
            fh = h // rows
            # Hàng 0=up, 1=down, 2=left, 3=right
            row_dirs = {0: 'up', 1: 'down', 2: 'left', 3: 'right'}
            target = cls.YELLOW_SPRITE_SIZE

            for r in range(rows):
                direction = row_dirs[r]
                # Quét cột chứa pixel thực tế trong hàng này
                active_cols = []
                for x in range(w):
                    has_px = False
                    for y in range(r * fh, (r + 1) * fh):
                        c = img.get_at((x, y))
                        r2, g2, b2, a2 = c
                        # Bỏ pixel trong suốt hoặc rất sáng (outline trắng)
                        if a2 > 10 and not (r2 > 235 and g2 > 235 and b2 > 235):
                            has_px = True
                            break
                    active_cols.append(has_px)

                # Tìm các đoạn liên tục
                segments = []
                in_segment = False
                start_x = 0
                for x in range(w):
                    if active_cols[x] and not in_segment:
                        in_segment = True
                        start_x = x
                    elif not active_cols[x] and in_segment:
                        in_segment = False
                        segments.append((start_x, x - 1))
                if in_segment:
                    segments.append((start_x, w - 1))

                # Lọc bỏ nhiễu có bề rộng quá nhỏ (nhỏ hơn 30 pixel)
                valid_segs = [(sx, ex) for (sx, ex) in segments if (ex - sx + 1) >= 30]

                # Giới hạn tối đa 6 frame cho walk cycle để tránh lấy nhầm frame có muzzle flash
                valid_segs = valid_segs[:6]

                frames = []
                for (sx_seg, ex_seg) in valid_segs:
                    # Cắt sprite theo chiều rộng thực tế của phân đoạn
                    sub_w = ex_seg - sx_seg + 1
                    sub = img.subsurface(pygame.Rect(sx_seg, r * fh, sub_w, fh)).copy()

                    # Làm sạch nền và lấy bounding box đứng chính xác
                    raw = pygame.Surface((sub_w, fh), pygame.SRCALPHA)
                    min_x, min_y, max_x, max_y = sub_w, fh, 0, 0
                    has_pixel = False

                    for yi in range(fh):
                        for xi in range(sub_w):
                            c = sub.get_at((xi, yi))
                            r2, g2, b2, a2 = c
                            if a2 > 10 and not (r2 > 235 and g2 > 235 and b2 > 235):
                                raw.set_at((xi, yi), (r2, g2, b2, a2))
                                min_x = min(min_x, xi); min_y = min(min_y, yi)
                                max_x = max(max_x, xi); max_y = max(max_y, yi)
                                has_pixel = True

                    if not has_pixel:
                        continue

                    # Cắt sát biên (bounding box crop)
                    content_w = max_x - min_x + 1
                    content_h = max_y - min_y + 1
                    content = raw.subsurface(pygame.Rect(min_x, min_y, content_w, content_h)).copy()

                    # Scale về kích thước mục tiêu mượt mà
                    scale = min(target / content_w, target / content_h)
                    new_w = max(1, int(content_w * scale))
                    new_h = max(1, int(content_h * scale))
                    scaled = pygame.transform.smoothscale(content, (new_w, new_h))

                    # Vẽ căn giữa khung hình
                    frame_surf = pygame.Surface((target, target), pygame.SRCALPHA)
                    ox2 = (target - new_w) // 2
                    oy2 = target - new_h
                    frame_surf.blit(scaled, (ox2, oy2))
                    frames.append(frame_surf)

                if frames:
                    cls._yellow_walk_frames[direction] = frames

            # Điền fallback cho các hướng thiếu
            for d in ['down', 'up', 'right', 'left']:
                if not cls._yellow_walk_frames.get(d):
                    cls._yellow_walk_frames[d] = [pygame.Surface((target, target), pygame.SRCALPHA)]
                cls._yellow_idle_frames[d] = cls._yellow_walk_frames[d][0]

            cls._yellow_sprites_loaded = True
        except Exception as e:
            print(f"[WARN] Không load được sprite robot vàng: {e}")
            cls._yellow_sprites_loaded = False

    @classmethod
    def _load_blue_sprites(cls):
        """Load và cắt sprite sheet robot xanh trời thành từng frame theo hướng"""
        if cls._blue_sprites_loaded:
            return
        base = os.path.dirname(os.path.abspath(__file__))
        sprite_path = os.path.join(base, "53400032-5b67-479a-9406-253fcffdb61f.jpg")
        try:
            img = pygame.image.load(sprite_path).convert_alpha()
            w, h = img.get_width(), img.get_height()
            # Sprite sheet: 8 cột × 4 hàng, lấy nửa trái (4 cột)
            cols_total, rows = 8, 4
            fw, fh = w // cols_total, h // rows
            bg_threshold = 200

            def extract_frame(col, row):
                sub = img.subsurface(pygame.Rect(col * fw, row * fh, fw, fh)).copy()
                result = pygame.Surface((fw, fh), pygame.SRCALPHA)
                for yi in range(fh):
                    for xi in range(fw):
                        color = sub.get_at((xi, yi))
                        if color[0] > bg_threshold and color[1] > bg_threshold and color[2] > bg_threshold:
                            continue
                        result.set_at((xi, yi), color)
                return pygame.transform.smoothscale(result, (cls.BLUE_SPRITE_SIZE, cls.BLUE_SPRITE_SIZE))

            # Hàng 0: Xuống, Hàng 1: Lên, Hàng 2: Phải, Hàng 3: Trái
            cls._blue_walk_frames['down']  = [extract_frame(c, 0) for c in range(4)]
            cls._blue_walk_frames['up']    = [extract_frame(c, 1) for c in range(4)]
            cls._blue_walk_frames['right'] = [extract_frame(c, 2) for c in range(4)]
            cls._blue_walk_frames['left']  = [extract_frame(c, 3) for c in range(4)]

            for d in ['down', 'up', 'right', 'left']:
                cls._blue_idle_frames[d] = cls._blue_walk_frames[d][0]

            cls._blue_sprites_loaded = True
        except Exception as e:
            print(f"[WARN] Không load được sprite robot xanh: {e}")
            cls._blue_sprites_loaded = False

    @classmethod
    def _load_giant_sprites(cls):
        if cls._giant_sprites_loaded:
            return
        base = os.path.dirname(os.path.abspath(__file__))
        sprite_path = os.path.join(base, "khổng lồ.png")
        try:
            img = pygame.image.load(sprite_path).convert_alpha()
            w, h = img.get_width(), img.get_height()
            rows = 4
            fh = h // rows
            row_dirs = {0: 'down', 1: 'left', 2: 'right', 3: 'up'}
            target = cls.GIANT_SPRITE_SIZE
            for r in range(rows):
                direction = row_dirs[r]
                fw = w // 8
                frames = []
                for c in range(8):
                    sub = img.subsurface(pygame.Rect(c*fw, r*fh, fw, fh)).copy()
                    min_x, min_y, max_x, max_y = fw, fh, 0, 0
                    has_pixel = False
                    for yi in range(fh):
                        for xi in range(fw):
                            if sub.get_at((xi, yi))[3] > 10:
                                min_x = min(min_x, xi); min_y = min(min_y, yi)
                                max_x = max(max_x, xi); max_y = max(max_y, yi)
                                has_pixel = True
                    if not has_pixel:
                        continue
                    content_w = max_x - min_x + 1
                    content_h = max_y - min_y + 1
                    content = sub.subsurface(pygame.Rect(min_x, min_y, content_w, content_h)).copy()
                    
                    scale = min(target / content_w, target / content_h)
                    new_w = max(1, int(content_w * scale))
                    new_h = max(1, int(content_h * scale))
                    scaled = pygame.transform.smoothscale(content, (new_w, new_h))
                    
                    frame_surf = pygame.Surface((target, target), pygame.SRCALPHA)
                    ox2 = (target - new_w) // 2
                    oy2 = target - new_h
                    frame_surf.blit(scaled, (ox2, oy2))
                    frames.append(frame_surf)
                
                if frames:
                    cls._giant_walk_frames[direction] = frames
            
            for d in ['down', 'up', 'right', 'left']:
                if not cls._giant_walk_frames.get(d):
                    cls._giant_walk_frames[d] = [pygame.Surface((target, target), pygame.SRCALPHA)]
                cls._giant_idle_frames[d] = cls._giant_walk_frames[d][0]
                
            cls._giant_sprites_loaded = True
        except Exception as e:
            print(f"[WARN] Không load được sprite khổng lồ: {e}")
            cls._giant_sprites_loaded = False

    @classmethod
    def _load_green_sprites(cls):
        """Load sprite sheet robot xanh lá từ 'quái xanh.png' (6 cột × 4 hàng, nền trong suốt sẵn)"""
        if cls._green_sprites_loaded:
            return
        import unicodedata
        base = os.path.dirname(os.path.abspath(__file__))
        
        # Thử tìm file theo nhiều cách để tránh lỗi encoding tiếng Việt trên Windows
        sprite_path = None
        target_names = ["quái xanh.png", "quai xanh.png", "quái_xanh.png", "quai_xanh.png", "unnamed (2).jpg"]
        
        # 1. Quét thư mục base và so khớp unicode chuẩn hóa
        try:
            if os.path.exists(base):
                for f in os.listdir(base):
                    f_nfc = unicodedata.normalize('NFC', f)
                    f_nfd = unicodedata.normalize('NFD', f)
                    matched = False
                    for t in target_names:
                        t_nfc = unicodedata.normalize('NFC', t)
                        t_nfd = unicodedata.normalize('NFD', t)
                        if f_nfc in [t_nfc, t_nfd] or f_nfd in [t_nfc, t_nfd]:
                            sprite_path = os.path.join(base, f)
                            matched = True
                            break
                    if matched:
                        break
        except Exception:
            pass

        # 2. Nếu quét không ra, thử các đường dẫn trực tiếp
        if not sprite_path:
            for name in target_names:
                p = os.path.join(base, name)
                if os.path.exists(p):
                    sprite_path = p
                    break
                p_cwd = name
                if os.path.exists(p_cwd):
                    sprite_path = p_cwd
                    break

        # 3. Nếu vẫn không thấy, mặc định là quái xanh.png trong base
        if not sprite_path:
            sprite_path = os.path.join(base, "quái xanh.png")
        
        try:
            img = pygame.image.load(sprite_path).convert_alpha()
            w, h = img.get_width(), img.get_height()
            fh = h // 4
            row_dirs = {0: 'up', 1: 'down', 2: 'right', 3: 'left'}

            for r in range(4):
                direction = row_dirs[r]
                row_y = r * fh
                
                # 1. Chiếu kênh alpha để tìm các cột chứa điểm ảnh của robot
                active_cols = []
                for x in range(w):
                    has_alpha = False
                    for y in range(row_y, row_y + fh):
                        if img.get_at((x, y))[3] > 10:
                            has_alpha = True
                            break
                    active_cols.append(has_alpha)
                
                # 2. Phát hiện các phân đoạn cột liên tục
                segments = []
                in_segment = False
                start_x = 0
                for x in range(w):
                    if active_cols[x] and not in_segment:
                        in_segment = True
                        start_x = x
                    elif not active_cols[x] and in_segment:
                        in_segment = False
                        segments.append((start_x, x - 1))
                if in_segment:
                    segments.append((start_x, w - 1))
                
                # 3. Gộp các mảnh vụn quá gần nhau (khoảng cách giữa các cột có nét vẽ < 12px)
                merged = []
                for seg in segments:
                    if not merged:
                        merged.append(seg)
                    else:
                        prev = merged[-1]
                        if seg[0] - prev[1] < 12:
                            merged[-1] = (prev[0], seg[1])
                        else:
                            merged.append(seg)
                
                # 4. Tách các phân đoạn dính nhau (nếu bề ngang segment > 130px thì chắc chắn có 2 con đứng sát nhau)
                final_segments = []
                for x0, x1 in merged:
                    width = x1 - x0 + 1
                    if width > 130:
                        half_w = width // 2
                        final_segments.append((x0, x0 + half_w - 1))
                        final_segments.append((x0 + half_w, x1))
                    else:
                        final_segments.append((x0, x1))
                
                # 5. Cắt chính xác từng con robot và căn chỉnh
                frames = []
                for x0, x1 in final_segments:
                    # Ràng buộc tọa độ
                    x0 = max(0, x0)
                    x1 = min(w - 1, x1)
                    sw = x1 - x0 + 1
                    if sw < 10:  # Bỏ qua các vệt nhiễu nhỏ
                        continue
                    
                    sub = img.subsurface(pygame.Rect(x0, row_y, sw, fh)).copy()
                    
                    # Tìm bounding box thực tế bên trong để căn đáy chân không bị rung lắc
                    min_x, min_y = sw, fh
                    max_x, max_y = 0, 0
                    has_content = False
                    for yi in range(fh):
                        for xi in range(sw):
                            if sub.get_at((xi, yi))[3] > 10:
                                min_x = min(min_x, xi)
                                min_y = min(min_y, yi)
                                max_x = max(max_x, xi)
                                max_y = max(max_y, yi)
                                has_content = True
                    
                    if not has_content:
                        continue
                    
                    content_w = max_x - min_x + 1
                    content_h = max_y - min_y + 1
                    content = sub.subsurface(pygame.Rect(min_x, min_y, content_w, content_h)).copy()
                    
                    # Scale theo kích thước GREEN_SPRITE_SIZE
                    target = cls.GREEN_SPRITE_SIZE
                    scale = min(target / content_w, target / content_h)
                    new_w = max(1, int(content_w * scale))
                    new_h = max(1, int(content_h * scale))
                    scaled = pygame.transform.smoothscale(content, (new_w, new_h))
                    
                    # Đặt vào tâm ngang, hạ sát đáy dọc
                    result = pygame.Surface((target, target), pygame.SRCALPHA)
                    ox = (target - new_w) // 2
                    oy = target - new_h
                    result.blit(scaled, (ox, oy))
                    frames.append(result)
                
                # Gán hoạt ảnh bước đi cho hướng tương ứng
                cls._green_walk_frames[direction] = frames

            # Đảm bảo tất cả hướng đều có ít nhất 1 frame
            for d in ['down', 'up', 'right', 'left']:
                if not cls._green_walk_frames.get(d):
                    cls._green_walk_frames[d] = [pygame.Surface((cls.GREEN_SPRITE_SIZE, cls.GREEN_SPRITE_SIZE), pygame.SRCALPHA)]
                cls._green_idle_frames[d] = cls._green_walk_frames[d][0]

            cls._green_sprites_loaded = True
        except Exception as e:
            print(f"[WARN] Không load được sprite robot xanh lá: {e}")
            cls._green_sprites_loaded = False

    def __init__(self, x, y, rtype='blue'):
        self.x, self.y = float(x), float(y)
        cfg = ROBOT_CONFIGS[rtype]
        self.rtype = rtype
        self.color = cfg['color']
        self.hp = cfg['hp']
        self.max_hp = cfg['hp']
        self.speed = cfg['speed']
        self.radius = cfg['radius']
        self.dmg = cfg['dmg']
        self.fear_light = cfg['fear_light']
        self.alive = True
        self.stun_timer = 0
        self.blind_timer = 0
        self.attack_cd = 0
        self.dir_angle = random.uniform(0, math.pi * 2)
        self.wander_timer = random.uniform(1, 3)
        # === ANIMATION STATE ===
        self.facing = 'down'
        self.anim_frame = 0
        self.anim_timer = 0.0
        self.anim_speed = 0.12 if rtype == 'green' else 0.15  # 6 frames cần nhanh hơn để cycle mượt
        self.is_moving = False
        self.walk_bob = 0.0        # Hiệu ứng nhún lên-xuống khi đi bộ (smooth bobbing)
        self.recoil_bob = 0.0      # Giật lùi nhẹ khi bắn súng
        self.punch_timer = 0.0     # Timer animation đấm tay (0.6s)
        self.punch_angle = 0.0     # Góc đấm hướng về player
        self.aggro_timer = 0.0     # Timer tức giận khi bị bắn (đuổi xa hơn, nhanh hơn)
        self.hit_flash_timer = 0.0 # Timer nhấp nháy đỏ khi trúng đạn
        
        # === BẮN SÚNG (cho robot xanh lá) ===
        self.shoot_cd = random.uniform(1.0, 2.5)
        self.burst_count = 0
        self.burst_timer = 0.0
        self.muzzle_flash_timer = 0.0
        self.shoot_angle = 0.0

        # === TACTICAL MOVEMENT (robot xanh lá) ===
        self.strafe_dir = random.choice([-1, 1])   # Hướng strafe: -1 trái, +1 phải
        self.strafe_timer = random.uniform(0.8, 2.0)  # Timer đổi hướng strafe
        self.flank_timer = 0.0          # Timer để robot vòng vây thay vì tiến thẳng
        self.patrol_angle = random.uniform(0, math.pi * 2)  # Góc tuần tra
        self.shoot_anim_timer = 0.0    # Timer chạy animation khi bắn

        # === LIGHTNING EFFECT (robot vàng) ===
        self.lightning_timer = random.uniform(0, 1.5)  # Timer nhấp nháy tia sét
        self.lightning_phase = 0.0                      # Phase animation sét

        # === DFS PATHFINDING CACHE (for all robots) ===
        self.dfs_path = []          # List waypoints [(wx, wy), ...]
        self.dfs_refresh = 1.2      # Recompute every 1.2 seconds
        self.dfs_timer = random.uniform(0.0, self.dfs_refresh)  # Staggered initial compute time

        # Load sprites tương ứng
        if self.rtype == 'blue':
            Robot._load_blue_sprites()
        elif self.rtype == 'green':
            Robot._load_green_sprites()
        elif self.rtype == 'white_giant':
            Robot._load_giant_sprites()
        elif self.rtype == 'yellow':
            Robot._load_yellow_sprites()

    def _get_dfs_move_angle(self, player, walls, map_w, map_h, dt):
        """Return the angle towards the next DFS waypoint if a path exists, else None."""
        if pf_dfs:
            self.dfs_timer -= dt
            if self.dfs_timer <= 0 or not self.dfs_path:
                self.dfs_path = pf_dfs(
                    (self.x, self.y), (player.x, player.y),
                    walls, map_w, map_h
                )
                self.dfs_timer = self.dfs_refresh
            if self.dfs_path:
                wx, wy = self.dfs_path[0]
                # Check if we have arrived close to the waypoint
                if math.hypot(wx - self.x, wy - self.y) < 20:
                    self.dfs_path.pop(0)
                    if self.dfs_path:
                        wx, wy = self.dfs_path[0]
                return math.atan2(wy - self.y, wx - self.x)
        return None

    def update(self, player, walls, dt, in_light=False, robots=None, map_w=MAP_W, map_h=MAP_H):
        if not self.alive:
            return None
        if self.stun_timer > 0:
            self.stun_timer -= dt
            return None
        if self.blind_timer > 0:
            self.blind_timer -= dt
            self.x += math.cos(self.dir_angle) * self.speed * 0.3
            self.y += math.sin(self.dir_angle) * self.speed * 0.3
            self._clamp(map_w, map_h)
            return None
        if self.attack_cd > 0:
            self.attack_cd -= dt
        if self.punch_timer > 0:
            self.punch_timer -= dt
        if self.aggro_timer > 0:
            self.aggro_timer -= dt
        if self.hit_flash_timer > 0:
            self.hit_flash_timer -= dt
        if self.shoot_cd > 0:
            self.shoot_cd -= dt
        if self.muzzle_flash_timer > 0:
            self.muzzle_flash_timer -= dt

        dist = math.hypot(player.x - self.x, player.y - self.y)
        angle_to_player = math.atan2(player.y - self.y, player.x - self.x)
        shot_bullet = None

        # Get DFS path angle if available
        dfs_angle = self._get_dfs_move_angle(player, walls, map_w, map_h, dt)

        # Lưu vị trí cũ để xác định hướng di chuyển cho animation
        old_x, old_y = self.x, self.y

        if self.rtype == 'blue':
            # Khi bị bắn trúng: tức giận, đuổi xa hơn và nhanh hơn!
            is_aggro = self.aggro_timer > 0
            chase_range = 600 if is_aggro else 300
            chase_speed = self.speed * 1.8 if is_aggro else self.speed

            if in_light and self.fear_light and not is_aggro:
                flee_angle = angle_to_player + math.pi
                mx = math.cos(flee_angle) * self.speed * 1.5
                my = math.sin(flee_angle) * self.speed * 1.5
                nx, ny = self.x + mx, self.y + my
                if not self._hit_wall(nx, self.y, walls): self.x = nx
                if not self._hit_wall(self.x, ny, walls): self.y = ny
            elif (player.light_on or is_aggro) and dist < chase_range:
                move_angle = dfs_angle if dfs_angle is not None else angle_to_player
                step_x = math.cos(move_angle) * chase_speed
                step_y = math.sin(move_angle) * chase_speed
                nx, ny = self.x + step_x, self.y + step_y
                if not self._hit_wall(nx, self.y, walls): self.x = nx
                if not self._hit_wall(self.x, ny, walls): self.y = ny
            else:
                self.dfs_path = []  # Reset path khi không đuổi
                self._wander(walls, dt)

        elif self.rtype in ['white', 'boss']:
            if (player.light_on or self.aggro_timer > 0) and dist < 350:
                move_angle = dfs_angle if dfs_angle is not None else angle_to_player
                mx = math.cos(move_angle) * self.speed
                my = math.sin(move_angle) * self.speed
                nx, ny = self.x + mx, self.y + my
                if not self._hit_wall(nx, self.y, walls): self.x = nx
                if not self._hit_wall(self.x, ny, walls): self.y = ny
            else:
                self.dfs_path = []  # Reset path khi không đuổi
                self._wander(walls, dt)
                
        elif self.rtype == 'white_giant':
            # Giant AI: Di chuyển 4 hướng chiến thuật, giữ khoảng cách bắn súng 6 nòng
            if (player.light_on or self.aggro_timer > 0) and dist < 600:
                self.strafe_timer -= dt
                if self.strafe_timer <= 0:
                    self.strafe_dir = random.choice([-1, 1])
                    self.strafe_timer = random.uniform(1.0, 2.5)

                perp_angle = angle_to_player + math.pi / 2 * self.strafe_dir

                if self.burst_count > 0:
                    # Đang bắn -> di chuyển chậm lại
                    sx_m = math.cos(perp_angle) * self.speed * 0.4
                    sy_m = math.sin(perp_angle) * self.speed * 0.4
                    nx, ny = self.x + sx_m, self.y + sy_m
                    if not self._hit_wall(nx, self.y, walls): self.x = nx
                    if not self._hit_wall(self.x, ny, walls): self.y = ny
                elif dist > 350:
                    # Đuổi theo: dùng đường dẫn DFS nếu có
                    move_angle = dfs_angle if dfs_angle is not None else angle_to_player
                    chase_x = math.cos(move_angle) * self.speed * 0.8
                    chase_y = math.sin(move_angle) * self.speed * 0.8
                    nx, ny = self.x + chase_x, self.y + chase_y
                    if not self._hit_wall(nx, self.y, walls): self.x = nx
                    if not self._hit_wall(self.x, ny, walls): self.y = ny
                elif dist < 250:
                    retreat_x = math.cos(angle_to_player + math.pi) * self.speed * 0.6
                    retreat_y = math.sin(angle_to_player + math.pi) * self.speed * 0.6
                    nx, ny = self.x + retreat_x, self.y + retreat_y
                    if not self._hit_wall(nx, self.y, walls): self.x = nx
                    if not self._hit_wall(self.x, ny, walls): self.y = ny
                else:
                    sx_m = math.cos(perp_angle) * self.speed * 0.7
                    sy_m = math.sin(perp_angle) * self.speed * 0.7
                    nx, ny = self.x + sx_m, self.y + sy_m
                    if not self._hit_wall(nx, self.y, walls): self.x = nx
                    if not self._hit_wall(self.x, ny, walls): self.y = ny

                # Kích hoạt bắn 3 viên liên tiếp mỗi 3 giây
                if self.shoot_cd <= 0 and self.burst_count == 0:
                    self.burst_count = 3
                    self.burst_timer = 0.0
                    self.shoot_cd = 3.0
            else:
                self.dfs_path = []  # Reset path khi không đuổi
                self._wander(walls, dt)
                
            # Xử lý bắn burst của khổng lồ
            if self.burst_count > 0:
                self.burst_timer -= dt
                if self.burst_timer <= 0:
                    muzzle_x, muzzle_y = self.x, self.y
                    if self.facing == 'right':
                        muzzle_x, muzzle_y = self.x + 40, self.y + 10
                    elif self.facing == 'left':
                        muzzle_x, muzzle_y = self.x - 40, self.y + 10
                    elif self.facing == 'down':
                        muzzle_x, muzzle_y = self.x + 15, self.y + 40
                    elif self.facing == 'up':
                        muzzle_x, muzzle_y = self.x - 15, self.y - 40
                        
                    shot_bullet = Bullet(muzzle_x, muzzle_y, angle_to_player, 'advanced_sniper', is_enemy=True, dmg=25)
                    self.muzzle_flash_timer = 0.2
                    self.shoot_angle = angle_to_player
                    self.shoot_anim_timer = 0.3
                    self.x -= math.cos(angle_to_player) * 4.0
                    self.y -= math.sin(angle_to_player) * 4.0
                    self.recoil_bob = 8.0
                    self.burst_count -= 1
                    self.burst_timer = 0.15 # Tốc độ xả đạn nhanh giữa các viên

        elif self.rtype == 'yellow':
            # === TACTICAL AI: Robot vàng - mạnh, strafe + burst 4 viên ===
            self.lightning_timer -= dt
            if self.lightning_timer <= 0:
                self.lightning_timer = random.uniform(0.6, 1.8)  # Tia sét nhấp nháy
            self.lightning_phase += dt * 8.0

            if (player.light_on or self.aggro_timer > 0) and dist < 550:
                self.strafe_timer -= dt
                if self.strafe_timer <= 0:
                    self.strafe_dir = random.choice([-1, 1])
                    self.strafe_timer = random.uniform(0.6, 1.5)

                perp_angle = angle_to_player + math.pi / 2 * self.strafe_dir

                if self.burst_count > 0:
                    # Đang bắn: strafe mạnh để né
                    sx_m = math.cos(perp_angle) * self.speed * 0.9
                    sy_m = math.sin(perp_angle) * self.speed * 0.9
                    if dist < 160:
                        sx_m += math.cos(angle_to_player + math.pi) * self.speed * 0.6
                        sy_m += math.sin(angle_to_player + math.pi) * self.speed * 0.6
                    elif dist > 320:
                        move_angle = dfs_angle if dfs_angle is not None else angle_to_player
                        sx_m += math.cos(move_angle) * self.speed * 0.5
                        sy_m += math.sin(move_angle) * self.speed * 0.5
                    nx, ny = self.x + sx_m, self.y + sy_m
                    if not self._hit_wall(nx, self.y, walls): self.x = nx
                    if not self._hit_wall(self.x, ny, walls): self.y = ny
                elif dist > 280:
                    # Đuổi theo: dùng đường dẫn DFS nếu có
                    move_angle = dfs_angle if dfs_angle is not None else angle_to_player
                    chase_x = math.cos(move_angle) * self.speed * 0.9
                    chase_y = math.sin(move_angle) * self.speed * 0.9
                    strafe_x = math.cos(perp_angle) * self.speed * 0.5
                    strafe_y = math.sin(perp_angle) * self.speed * 0.5
                    nx, ny = self.x + chase_x + strafe_x, self.y + chase_y + strafe_y
                    if not self._hit_wall(nx, self.y, walls): self.x = nx
                    if not self._hit_wall(self.x, ny, walls): self.y = ny
                elif dist < 130:
                    retreat_x = math.cos(angle_to_player + math.pi) * self.speed
                    retreat_y = math.sin(angle_to_player + math.pi) * self.speed
                    strafe_x = math.cos(perp_angle) * self.speed * 0.6
                    strafe_y = math.sin(perp_angle) * self.speed * 0.6
                    nx, ny = self.x + retreat_x + strafe_x, self.y + retreat_y + strafe_y
                    if not self._hit_wall(nx, self.y, walls): self.x = nx
                    if not self._hit_wall(self.x, ny, walls): self.y = ny
                else:
                    sx_m = math.cos(perp_angle) * self.speed
                    sy_m = math.sin(perp_angle) * self.speed
                    nx, ny = self.x + sx_m, self.y + sy_m
                    if not self._hit_wall(nx, self.y, walls): self.x = nx
                    if not self._hit_wall(self.x, ny, walls): self.y = ny

                # Kích hoạt bắn 1 viên mỗi 0.75 giây (Yellow robot)
                if self.shoot_cd <= 0 and self.burst_count == 0:
                    self.burst_count = 1
                    self.burst_timer = 0.0
                    self.shoot_cd = 0.75
            else:
                self.dfs_path = []  # Reset path khi không đuổi
                self._wander(walls, dt)

            # Xử lý bắn burst của robot vàng
            if self.burst_count > 0:
                self.burst_timer -= dt
                if self.burst_timer <= 0:
                    muzzle_x, muzzle_y = self.x, self.y
                    if self.facing == 'right':
                        muzzle_x, muzzle_y = self.x + 26, self.y
                    elif self.facing == 'left':
                        muzzle_x, muzzle_y = self.x - 26, self.y
                    elif self.facing == 'down':
                        muzzle_x, muzzle_y = self.x + 12, self.y + 20
                    elif self.facing == 'up':
                        muzzle_x, muzzle_y = self.x - 12, self.y - 20
                    # Đạn vàng mạnh hơn (dmg=18)
                    shot_bullet = Bullet(muzzle_x, muzzle_y, angle_to_player, 'pistol', is_enemy=True, dmg=18)
                    self.muzzle_flash_timer = 0.15
                    self.shoot_angle = angle_to_player
                    self.shoot_anim_timer = 0.25
                    self.x -= math.cos(angle_to_player) * 3.0
                    self.y -= math.sin(angle_to_player) * 3.0
                    self.recoil_bob = 5.5
                    self.burst_count -= 1
                    self.burst_timer = 0.11

        elif self.rtype == 'green':
            # === TACTICAL AI: Robot xanh lá di chuyển chiến thuật 4 hướng ===
            if (player.light_on or self.aggro_timer > 0) and dist < 500:
                # --- Cập nhật timer tactical ---
                self.strafe_timer -= dt
                if self.strafe_timer <= 0:
                    self.strafe_dir = random.choice([-1, 1])
                    self.strafe_timer = random.uniform(0.7, 1.8)

                # Góc vuông góc (strafe perpendicular to player)
                perp_angle = angle_to_player + math.pi / 2 * self.strafe_dir

                if self.burst_count > 0:
                    # Đang bắn: vừa strafe ngang vừa giữ khoảng cách
                    strafe_speed = self.speed * 0.7
                    sx_m = math.cos(perp_angle) * strafe_speed
                    sy_m = math.sin(perp_angle) * strafe_speed
                    # Giữ khoảng cách tối ưu 180-280px
                    if dist < 180:
                        sx_m += math.cos(angle_to_player + math.pi) * self.speed * 0.5
                        sy_m += math.sin(angle_to_player + math.pi) * self.speed * 0.5
                    elif dist > 300:
                        move_angle = dfs_angle if dfs_angle is not None else angle_to_player
                        sx_m += math.cos(move_angle) * self.speed * 0.4
                        sy_m += math.sin(move_angle) * self.speed * 0.4
                    nx, ny = self.x + sx_m, self.y + sy_m
                    if not self._hit_wall(nx, self.y, walls): self.x = nx
                    if not self._hit_wall(self.x, ny, walls): self.y = ny
                elif dist > 260:
                    # Tiến về phía player kết hợp strafe nhẹ (dùng DFS)
                    move_angle = dfs_angle if dfs_angle is not None else angle_to_player
                    chase_x = math.cos(move_angle) * self.speed * 0.85
                    chase_y = math.sin(move_angle) * self.speed * 0.85
                    strafe_x = math.cos(perp_angle) * self.speed * 0.4
                    strafe_y = math.sin(perp_angle) * self.speed * 0.4
                    mx = chase_x + strafe_x
                    my = chase_y + strafe_y
                    nx, ny = self.x + mx, self.y + my
                    if not self._hit_wall(nx, self.y, walls): self.x = nx
                    if not self._hit_wall(self.x, ny, walls): self.y = ny
                elif dist < 150:
                    # Quá gần: lùi lại + strafe
                    retreat_x = math.cos(angle_to_player + math.pi) * self.speed * 0.9
                    retreat_y = math.sin(angle_to_player + math.pi) * self.speed * 0.9
                    strafe_x = math.cos(perp_angle) * self.speed * 0.5
                    strafe_y = math.sin(perp_angle) * self.speed * 0.5
                    nx, ny = self.x + retreat_x + strafe_x, self.y + retreat_y + strafe_y
                    if not self._hit_wall(nx, self.y, walls): self.x = nx
                    if not self._hit_wall(self.x, ny, walls): self.y = ny
                else:
                    # Khoảng cách lý tưởng: thuần strafe
                    sx_m = math.cos(perp_angle) * self.speed * 0.8
                    sy_m = math.sin(perp_angle) * self.speed * 0.8
                    nx, ny = self.x + sx_m, self.y + sy_m
                    if not self._hit_wall(nx, self.y, walls): self.x = nx
                    if not self._hit_wall(self.x, ny, walls): self.y = ny

                # Kích hoạt bắn 1 viên mỗi 1.25 giây (Green robot)
                if self.shoot_cd <= 0 and self.burst_count == 0:
                    self.burst_count = 1
                    self.burst_timer = 0.0
                    self.shoot_cd = 1.25
            else:
                self.dfs_path = []  # Reset path khi không đuổi
                self._wander(walls, dt)

            # Xử lý bắn đạn trong đợt burst
            if self.burst_count > 0:
                self.burst_timer -= dt
                if self.burst_timer <= 0:
                    # Xác định vị trí nòng súng theo hướng nhìn
                    muzzle_x, muzzle_y = self.x, self.y
                    if self.facing == 'right':
                        muzzle_x, muzzle_y = self.x + 24, self.y - 2
                    elif self.facing == 'left':
                        muzzle_x, muzzle_y = self.x - 24, self.y - 2
                    elif self.facing == 'down':
                        muzzle_x, muzzle_y = self.x + 10, self.y + 18
                    elif self.facing == 'up':
                        muzzle_x, muzzle_y = self.x - 10, self.y - 18

                    shot_bullet = Bullet(muzzle_x, muzzle_y, angle_to_player, 'pistol', is_enemy=True, dmg=12)
                    self.muzzle_flash_timer = 0.14
                    self.shoot_angle = angle_to_player
                    self.shoot_anim_timer = 0.25  # Chạy animation bắn 0.25s

                    # Hiệu ứng giật lùi
                    self.x -= math.cos(angle_to_player) * 2.5
                    self.y -= math.sin(angle_to_player) * 2.5
                    self.recoil_bob = 4.5

                    self.burst_count -= 1
                    self.burst_timer = 0.13

        self._resolve_wall_collision(walls)
        self._clamp(map_w, map_h)

        # === CẬP NHẬT HƯỚNG NHÌN VÀ ANIMATION SPRITE ===
        dx_moved = self.x - old_x
        dy_moved = self.y - old_y
        actually_moved = abs(dx_moved) > 0.01 or abs(dy_moved) > 0.01

        # Cập nhật facing dựa trên delta di chuyển thực tế cho TẤT CẢ robot
        if actually_moved:
            self.is_moving = True
        else:
            self.is_moving = False
            
        # Luôn luôn hướng mặt về phía người chơi khi nhìn thấy (đối với robot có súng), dù đang di chuyển hay đứng yên
        can_see_player = player.light_on or self.aggro_timer > 0
        if self.rtype in ['green', 'yellow', 'white_giant'] and dist < 600 and can_see_player:
            aim_deg = math.degrees(angle_to_player) % 360
            if 45 <= aim_deg < 135:
                self.facing = 'down'
            elif 135 <= aim_deg < 225:
                self.facing = 'left'
            elif 225 <= aim_deg < 315:
                self.facing = 'up'
            else:
                self.facing = 'right'
        elif actually_moved:
            if abs(dx_moved) > abs(dy_moved):
                self.facing = 'right' if dx_moved > 0 else 'left'
            else:
                self.facing = 'down' if dy_moved > 0 else 'up'

        # Giảm shoot_anim_timer
        if self.rtype in ['green', 'yellow', 'white_giant'] and self.shoot_anim_timer > 0:
            self.shoot_anim_timer -= dt

        # Cập nhật frame animation
        # Robot xanh lá và vàng: animate cả khi bắn (shoot_anim_timer > 0)
        is_animating = self.is_moving or (self.rtype in ['green', 'yellow', 'white_giant'] and self.shoot_anim_timer > 0)
        if is_animating:
            anim_spd = self.anim_speed if self.is_moving else 0.08  # Nhanh hơn khi bắn
            self.anim_timer += dt
            if self.anim_timer >= anim_spd:
                self.anim_timer = 0
                max_f = 4
                if self.rtype == 'green' and Robot._green_sprites_loaded:
                    frames_dict = Robot._green_walk_frames
                    if self.facing in frames_dict and frames_dict[self.facing]:
                        max_f = len(frames_dict[self.facing])
                elif self.rtype == 'yellow' and Robot._yellow_sprites_loaded:
                    frames_dict = Robot._yellow_walk_frames
                    if self.facing in frames_dict and frames_dict[self.facing]:
                        max_f = len(frames_dict[self.facing])
                elif self.rtype == 'blue' and Robot._blue_sprites_loaded:
                    frames_dict = Robot._blue_walk_frames
                    if self.facing in frames_dict and frames_dict[self.facing]:
                        max_f = len(frames_dict[self.facing])
                elif self.rtype == 'white_giant' and Robot._giant_sprites_loaded:
                    frames_dict = Robot._giant_walk_frames
                    if self.facing in frames_dict and frames_dict[self.facing]:
                        max_f = len(frames_dict[self.facing])
                self.anim_frame = (self.anim_frame + 1) % max_f
            if self.is_moving:
                self.walk_bob = math.sin(self.anim_timer / max(0.001, self.anim_speed) * math.pi + self.anim_frame * math.pi / 3) * 2.5
        else:
            self.anim_timer = 0
            # Hồi về vị trí chuẩn mượt mà
            self.walk_bob *= 0.82

        # Giảm dần recoil bob
        if self.recoil_bob > 0.1:
            self.recoil_bob *= 0.86
        else:
            self.recoil_bob = 0

        # Tấn công cận chiến bằng đấm tay khi gần player
        if dist < self.radius + player.radius + 5 and self.attack_cd <= 0:
            player.take_damage(self.dmg)
            self.attack_cd = 0.8 if self.aggro_timer > 0 else 1.0
            if self.rtype == 'blue':
                self.punch_timer = 0.6  # 0.6 giây animation đấm chân thật
                self.punch_angle = angle_to_player

        return shot_bullet

    def _wander(self, walls, dt):
        self.wander_timer -= dt
        if self.wander_timer <= 0:
            self.dir_angle = random.uniform(0, math.pi * 2)
            self.wander_timer = random.uniform(1, 3)
        mx = math.cos(self.dir_angle) * self.speed * 0.5
        my = math.sin(self.dir_angle) * self.speed * 0.5
        nx, ny = self.x + mx, self.y + my
        if not self._hit_wall(nx, self.y, walls): self.x = nx
        if not self._hit_wall(self.x, ny, walls): self.y = ny

    def _hit_wall(self, x, y, walls):
        r = self.radius
        rect = pygame.Rect(x - r, y - r, r * 2, r * 2)
        for w in walls:
            if rect.colliderect(w):
                return True
        return False

    def _clamp(self, map_w=MAP_W, map_h=MAP_H):
        self.x = max(self.radius, min(map_w - self.radius, self.x))
        self.y = max(self.radius, min(map_h - self.radius, self.y))

    def _resolve_wall_collision(self, walls):
        r = self.radius
        for _ in range(2):
            for w in walls:
                rect = pygame.Rect(self.x - r, self.y - r, r * 2, r * 2)
                if rect.colliderect(w):
                    overlap_x = min(rect.right, w.right) - max(rect.left, w.left)
                    overlap_y = min(rect.bottom, w.bottom) - max(rect.top, w.top)
                    if overlap_x < overlap_y:
                        if self.x < w.centerx:
                            self.x -= overlap_x
                        else:
                            self.x += overlap_x
                    else:
                        if self.y < w.centery:
                            self.y -= overlap_y
                        else:
                            self.y += overlap_y

    def take_damage(self, dmg):
        self.hp -= dmg
        self.hit_flash_timer = 0.15  # Nhấp nháy đỏ khi trúng đạn
        if self.hp > 0:
            self.aggro_timer = 8.0  # 8 giây tức giận
        if self.hp <= 0:
            self.hp = 0
            self.alive = False

    def draw(self, surf, cam_x, cam_y):
        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y)
        r = self.radius

        # === VẼ ROBOT XANH TRỜI BẰNG SPRITE ANIMATION + ĐẤM TAY CHÂN THẬT ===
        if self.rtype == 'blue' and Robot._blue_sprites_loaded:
            half = self.BLUE_SPRITE_SIZE // 2
            # Chọn frame phù hợp
            if self.is_moving and self.facing in Robot._blue_walk_frames:
                frames = Robot._blue_walk_frames[self.facing]
                frame = frames[self.anim_frame % len(frames)]
            elif self.facing in Robot._blue_idle_frames:
                frame = Robot._blue_idle_frames[self.facing]
            else:
                frame = Robot._blue_idle_frames.get('down')

            if frame:
                # Nhấp nháy đỏ khi trúng đạn
                if self.hit_flash_timer > 0:
                    tinted = frame.copy()
                    red_overlay = pygame.Surface(tinted.get_size(), pygame.SRCALPHA)
                    red_overlay.fill((255, 0, 0, 100))
                    tinted.blit(red_overlay, (0, 0))
                    surf.blit(tinted, (sx - half, sy - half))
                else:
                    surf.blit(frame, (sx - half, sy - half))

            # Vẽ mắt đỏ sáng rực khi tức giận (aggro)
            if self.aggro_timer > 0:
                glow_s = pygame.Surface((20, 12), pygame.SRCALPHA)
                pulse = 0.7 + 0.3 * math.sin(pygame.time.get_ticks() * 0.015)
                glow_alpha = int(180 * pulse)
                pygame.draw.circle(glow_s, (255, 30, 30, glow_alpha), (5, 6), 5)
                pygame.draw.circle(glow_s, (255, 30, 30, glow_alpha), (15, 6), 5)
                surf.blit(glow_s, (sx - 10, sy - half // 2 - 3))
                # Biểu tượng tức giận (💢) nhỏ phía trên đầu
                if int(pygame.time.get_ticks() / 400) % 2 == 0:
                    anger_f = _get_font(14)
                    anger_t = anger_f.render("💢", True, (255, 50, 50))
                    surf.blit(anger_t, (sx + half // 2 - 2, sy - half - 8))

            # === HIỆU ỨNG ĐẤM TAY 3 PHA CHÂN THẬT ===
            if self.punch_timer > 0:
                prog = 1.0 - (self.punch_timer / 0.6)  # 0.0 -> 1.0 (tiến trình)
                pa = self.punch_angle
                perp = pa + math.pi / 2

                # Pha 1: Wind-up (0.0 - 0.25) - Tay rút về phía sau, tích lực
                # Pha 2: Strike  (0.25 - 0.5) - Tay đấm ra phía trước cực nhanh
                # Pha 3: Follow-through (0.5 - 1.0) - Tay rút lại, hiệu ứng va chạm
                if prog < 0.25:
                    # Wind-up: tay rút ngược lại + tích năng lượng
                    t = prog / 0.25
                    extend = -0.4 * t  # Rút ngược
                    # Hào quang tích lực ở nắm đấm
                    charge_r = int(6 + t * 10)
                    charge_s = pygame.Surface((charge_r * 2, charge_r * 2), pygame.SRCALPHA)
                    pygame.draw.circle(charge_s, (100, 200, 255, int(60 * t)), (charge_r, charge_r), charge_r)
                    cx = sx + int(math.cos(pa) * (r - 5))
                    cy = sy + int(math.sin(pa) * (r - 5))
                    surf.blit(charge_s, (cx - charge_r, cy - charge_r))
                elif prog < 0.5:
                    # Strike: đấm ra cực nhanh!
                    t = (prog - 0.25) / 0.25
                    extend = -0.4 + 1.8 * t  # Từ -0.4 đến 1.4
                else:
                    # Follow-through: rút lại
                    t = (prog - 0.5) / 0.5
                    extend = 1.4 * (1.0 - t * t)  # Giảm dần

                # Tính vị trí vai, khuỷu tay, nắm đấm
                shoulder_dist = r - 2
                shoulder_off = 5  # Lệch khỏi trục chính
                shoulder_x = sx + int(math.cos(pa) * shoulder_dist) + int(math.cos(perp) * shoulder_off)
                shoulder_y = sy + int(math.sin(pa) * shoulder_dist) + int(math.sin(perp) * shoulder_off)

                elbow_dist = shoulder_dist + 8 + int(extend * 6)
                elbow_x = sx + int(math.cos(pa) * elbow_dist) + int(math.cos(perp) * 3)
                elbow_y = sy + int(math.sin(pa) * elbow_dist) + int(math.sin(perp) * 3)

                fist_dist = r + int(max(0, extend) * 24)
                fist_x = sx + int(math.cos(pa) * fist_dist)
                fist_y = sy + int(math.sin(pa) * fist_dist)

                # Vẽ cánh tay trên (vai → khuỷu)
                pygame.draw.line(surf, (40, 100, 180), (shoulder_x, shoulder_y), (elbow_x, elbow_y), 7)
                pygame.draw.line(surf, (60, 140, 220), (shoulder_x, shoulder_y), (elbow_x, elbow_y), 4)
                # Khớp khuỷu tay
                pygame.draw.circle(surf, (50, 120, 200), (elbow_x, elbow_y), 4)
                # Vẽ cẳng tay (khuỷu → nắm đấm)
                pygame.draw.line(surf, (50, 120, 200), (elbow_x, elbow_y), (fist_x, fist_y), 7)
                pygame.draw.line(surf, (80, 160, 240), (elbow_x, elbow_y), (fist_x, fist_y), 4)

                # Nắm đấm thép - hình vuông bo tròn xoay theo hướng đấm
                fist_sz = 10
                fist_pts = []
                for i in range(4):
                    corner_a = pa + math.pi / 4 + i * math.pi / 2
                    fist_pts.append((
                        fist_x + int(math.cos(corner_a) * fist_sz),
                        fist_y + int(math.sin(corner_a) * fist_sz)
                    ))
                pygame.draw.polygon(surf, (30, 70, 180), fist_pts)
                pygame.draw.polygon(surf, (80, 160, 255), fist_pts, 2)
                # Đinh tán trên nắm đấm
                pygame.draw.circle(surf, (150, 220, 255), (fist_x, fist_y), 3)
                pygame.draw.circle(surf, (220, 240, 255), (fist_x, fist_y), 1)

                # Vệt chuyển động (motion lines) trong pha Strike
                if 0.25 <= prog < 0.5:
                    t_strike = (prog - 0.25) / 0.25
                    for i in range(5):
                        line_off = (i - 2) * 5
                        trail_len = int(20 * t_strike)
                        lx = fist_x - int(math.cos(pa) * trail_len)
                        ly = fist_y - int(math.sin(pa) * trail_len)
                        lx += int(math.cos(perp) * line_off)
                        ly += int(math.sin(perp) * line_off)
                        alpha = int(200 * (1.0 - abs(i - 2) / 3.0) * t_strike)
                        line_s = pygame.Surface((trail_len + 4, 4), pygame.SRCALPHA)
                        pygame.draw.line(line_s, (200, 220, 255, alpha), (0, 2), (trail_len, 2), 2)
                        surf.blit(line_s, (min(lx, fist_x) - 2, min(ly, fist_y) - 2))

                # Hiệu ứng va chạm (Impact) khi đấm chạm đỉnh
                if 0.4 <= prog <= 0.65:
                    impact_t = (prog - 0.4) / 0.25
                    # Vòng sóng xung kích mở rộng
                    ring_r = int(8 + impact_t * 25)
                    ring_s = pygame.Surface((ring_r * 2 + 8, ring_r * 2 + 8), pygame.SRCALPHA)
                    ring_alpha = int(220 * (1.0 - impact_t))
                    pygame.draw.circle(ring_s, (255, 200, 50, ring_alpha), (ring_r + 4, ring_r + 4), ring_r, max(1, 4 - int(impact_t * 3)))
                    pygame.draw.circle(ring_s, (255, 255, 200, ring_alpha // 2), (ring_r + 4, ring_r + 4), ring_r // 2, max(1, 2))
                    surf.blit(ring_s, (fist_x - ring_r - 4, fist_y - ring_r - 4))
                    # Tia lửa bắn ra (sparks)
                    for i in range(6):
                        spark_a = pa + math.radians(random.randint(-60, 60))
                        spark_d = int(10 + impact_t * 18)
                        spk_x = fist_x + int(math.cos(spark_a) * spark_d)
                        spk_y = fist_y + int(math.sin(spark_a) * spark_d)
                        spark_s = pygame.Surface((6, 6), pygame.SRCALPHA)
                        pygame.draw.circle(spark_s, (255, 255, 100, ring_alpha), (3, 3), 2 + random.randint(0, 1))
                        surf.blit(spark_s, (spk_x - 3, spk_y - 3))

        # === VẼ ROBOT XANH LÁ BẰNG SPRITE ANIMATION + MUZZLE FLASH BẮN SÚNG ===
        elif self.rtype == 'green' and Robot._green_sprites_loaded:
            half = self.GREEN_SPRITE_SIZE // 2
            # Chọn frame phù hợp
            if self.is_moving and self.facing in Robot._green_walk_frames:
                frames = Robot._green_walk_frames[self.facing]
                frame = frames[self.anim_frame % len(frames)]
            elif self.facing in Robot._green_idle_frames:
                frame = Robot._green_idle_frames[self.facing]
            else:
                frame = Robot._green_idle_frames.get('down')

            if frame:
                # Tính vị trí vẽ với hiệu ứng nhún (walk bob) + giật lùi (recoil)
                draw_x = sx - half
                draw_y = sy - half - int(self.walk_bob)
                
                # Hiệu ứng giật lùi khi bắn (nhẹ nhàng, theo hướng ngược lại nòng súng)
                if self.recoil_bob > 0.5:
                    recoil_dir = self.shoot_angle + math.pi  # Ngược hướng bắn
                    draw_x += int(math.cos(recoil_dir) * self.recoil_bob)
                    draw_y += int(math.sin(recoil_dir) * self.recoil_bob)
                
                # Nhấp nháy đỏ khi bị trúng đạn
                if self.hit_flash_timer > 0:
                    tinted = frame.copy()
                    red_overlay = pygame.Surface(tinted.get_size(), pygame.SRCALPHA)
                    red_overlay.fill((255, 0, 0, 100))
                    tinted.blit(red_overlay, (0, 0))
                    surf.blit(tinted, (draw_x, draw_y))
                else:
                    surf.blit(frame, (draw_x, draw_y))

            # === HIỆU ỨNG LÓE SÁNG NÒNG SÚNG MƯỢT MÀ ĐẸP MẮT (MUZZLE FLASH) ===
            if self.muzzle_flash_timer > 0:
                fp = self.muzzle_flash_timer / 0.12  # 1.0 → 0.0 (tiến trình giảm dần)
                # Xác định nòng súng tương ứng theo hướng
                muzzle_x, muzzle_y = sx, sy
                if self.facing == 'right':
                    muzzle_x, muzzle_y = sx + 26, sy - 2
                elif self.facing == 'left':
                    muzzle_x, muzzle_y = sx - 26, sy - 2
                elif self.facing == 'down':
                    muzzle_x, muzzle_y = sx + 10, sy + 20
                elif self.facing == 'up':
                    muzzle_x, muzzle_y = sx - 10, sy - 20

                # --- 1. QUẦNG SÁNG MỜ LỚN (Outer Glow) ---
                glow_r = int(28 * fp)
                if glow_r > 2:
                    glow_s = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
                    pygame.draw.circle(glow_s, (255, 160, 30, int(80 * fp)), (glow_r, glow_r), glow_r)
                    pygame.draw.circle(glow_s, (255, 220, 80, int(50 * fp)), (glow_r, glow_r), glow_r * 2 // 3)
                    surf.blit(glow_s, (muzzle_x - glow_r, muzzle_y - glow_r))

                # --- 2. NGÔI SAO LỬA XOAY (Rotating Fire Star) ---
                fl_size = int(16 * fp)
                pts_outer = []
                pts_inner = []
                rot_offset = (1 - fp) * 3.0  # Xoay theo thời gian
                for i in range(10):
                    ang = self.shoot_angle + i * math.pi / 5 + rot_offset
                    l_out = fl_size * (1.3 if i % 2 == 0 else 0.5)
                    l_in = fl_size * (0.7 if i % 2 == 0 else 0.25)
                    pts_outer.append((muzzle_x + math.cos(ang) * l_out, muzzle_y + math.sin(ang) * l_out))
                    pts_inner.append((muzzle_x + math.cos(ang) * l_in, muzzle_y + math.sin(ang) * l_in))
                if len(pts_outer) > 2:
                    pygame.draw.polygon(surf, (255, 80, 0), pts_outer)       # Lớp cam đỏ ngoài
                    pygame.draw.polygon(surf, (255, 200, 30), pts_inner)     # Lớp vàng sáng trong
                    pygame.draw.circle(surf, (255, 255, 220), (muzzle_x, muzzle_y), max(1, int(5 * fp)))  # Nhân trắng rực

                # --- 3. TIA LỬA PHỤT HƯỚNG BẮN (Directional Flame Jet) ---
                beam_len = int(22 * fp)
                bx = muzzle_x + int(math.cos(self.shoot_angle) * beam_len)
                by = muzzle_y + int(math.sin(self.shoot_angle) * beam_len)
                pygame.draw.line(surf, (255, 200, 50), (muzzle_x, muzzle_y), (bx, by), max(1, int(4 * fp)))
                pygame.draw.line(surf, (255, 255, 200), (muzzle_x, muzzle_y), (bx, by), max(1, int(2 * fp)))
                # Tia lửa phụ hai bên
                perp = self.shoot_angle + math.pi / 2
                for side in [-1, 1]:
                    side_len = int(10 * fp)
                    side_x = muzzle_x + int(math.cos(self.shoot_angle) * 4) + int(math.cos(perp) * side * 5)
                    side_y = muzzle_y + int(math.sin(self.shoot_angle) * 4) + int(math.sin(perp) * side * 5)
                    end_x = side_x + int(math.cos(self.shoot_angle + side * 0.4) * side_len)
                    end_y = side_y + int(math.sin(self.shoot_angle + side * 0.4) * side_len)
                    pygame.draw.line(surf, (255, 150, 30, ), (side_x, side_y), (end_x, end_y), max(1, int(2 * fp)))

                # --- 4. TIA LỬA NHỎ VĂN NGẪU NHIÊN (Sparks) ---
                if fp > 0.5:
                    for _ in range(3):
                        spark_ang = self.shoot_angle + random.uniform(-0.8, 0.8)
                        spark_dist = random.randint(8, max(8, int(18 * fp)))
                        spk_x = muzzle_x + int(math.cos(spark_ang) * spark_dist)
                        spk_y = muzzle_y + int(math.sin(spark_ang) * spark_dist)
                        spk_r = random.randint(1, 3)
                        pygame.draw.circle(surf, (255, 255, 100), (spk_x, spk_y), spk_r)

                # --- 5. VỎ ĐẠN VĂNG RA (Shell Ejection) ---
                fly_dist = (1.0 - fp) * 20
                shell_perp = self.shoot_angle + math.pi / 2
                shell_x = int(muzzle_x - math.cos(self.shoot_angle) * 8 + math.cos(shell_perp) * fly_dist)
                shell_y = int(muzzle_y - math.sin(self.shoot_angle) * 8 + math.sin(shell_perp) * fly_dist)
                shell_y -= int((1.0 - fp) * 6)  # Bay lên theo parabol
                shell_ang = (1.0 - fp) * math.pi * 5
                s_ca, s_sa = math.cos(shell_ang), math.sin(shell_ang)
                slen, swid = 5, 2
                sp1 = (shell_x + s_ca * slen/2 + s_sa * swid/2, shell_y + s_sa * slen/2 - s_ca * swid/2)
                sp2 = (shell_x - s_ca * slen/2 + s_sa * swid/2, shell_y - s_sa * slen/2 - s_ca * swid/2)
                sp3 = (shell_x - s_ca * slen/2 - s_sa * swid/2, shell_y - s_sa * slen/2 + s_ca * swid/2)
                sp4 = (shell_x + s_ca * slen/2 - s_sa * swid/2, shell_y + s_sa * slen/2 + s_ca * swid/2)
                pygame.draw.polygon(surf, (255, 200, 50), [sp1, sp2, sp3, sp4])
                pygame.draw.polygon(surf, (200, 150, 20), [sp1, sp2, sp3, sp4], 1)

        # === VẼ ROBOT VÀNG BẰNG SPRITE ANIMATION CÓ TIA SÉT TRÊN ĐẦU ===
        elif self.rtype == 'yellow' and Robot._yellow_sprites_loaded:
            half = self.YELLOW_SPRITE_SIZE // 2
            # Chọn frame phù hợp
            if self.is_moving and self.facing in Robot._yellow_walk_frames:
                frames = Robot._yellow_walk_frames[self.facing]
                frame = frames[self.anim_frame % len(frames)]
            elif self.facing in Robot._yellow_idle_frames:
                frame = Robot._yellow_idle_frames[self.facing]
            else:
                frame = Robot._yellow_idle_frames.get('down')

            if frame:
                # Tính vị trí vẽ với hiệu ứng nhún (walk bob) + giật lùi (recoil)
                draw_x = sx - half
                draw_y = sy - half - int(self.walk_bob)
                
                # Hiệu ứng giật lùi khi bắn (nhẹ nhàng, theo hướng ngược lại nòng súng)
                if self.recoil_bob > 0.5:
                    recoil_dir = self.shoot_angle + math.pi  # Ngược hướng bắn
                    draw_x += int(math.cos(recoil_dir) * self.recoil_bob)
                    draw_y += int(math.sin(recoil_dir) * self.recoil_bob)
                
                # Nhấp nháy đỏ khi bị trúng đạn
                if self.hit_flash_timer > 0:
                    tinted = frame.copy()
                    red_overlay = pygame.Surface(tinted.get_size(), pygame.SRCALPHA)
                    red_overlay.fill((255, 0, 0, 100))
                    tinted.blit(red_overlay, (0, 0))
                    surf.blit(tinted, (draw_x, draw_y))
                else:
                    surf.blit(frame, (draw_x, draw_y))

            # === HIỆU ỨNG TIA SÉT TRÊN ĐẦU (LIGHTNING EFFECT) ===
            # Chỉ vẽ ziczac tia sét khi còn sống và theo phase nhấp nháy liên tục
            if self.alive and (int(self.lightning_phase) % 3 != 0):
                lightning_pts = []
                top_y = sy - half - 18
                bot_y = sy - half + 4
                segments = 3
                lightning_pts.append((sx, top_y))
                for i in range(1, segments):
                    prog = i / segments
                    seg_y = top_y + (bot_y - top_y) * prog
                    seg_x = sx + random.randint(-7, 7)
                    lightning_pts.append((seg_x, seg_y))
                lightning_pts.append((sx, bot_y))
                
                if len(lightning_pts) > 1:
                    # Đường viền sét sáng rực màu xanh neon/cyan phát sáng
                    pygame.draw.lines(surf, (0, 255, 255), False, lightning_pts, 3)
                    # Lõi trắng tinh
                    pygame.draw.lines(surf, (255, 255, 255), False, lightning_pts, 1)
                    # Quầng sáng nhẹ tại gốc sét tiếp xúc trên đầu robot
                    glow_r = random.randint(4, 7)
                    glow_s = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
                    pygame.draw.circle(glow_s, (0, 255, 255, 120), (glow_r, glow_r), glow_r)
                    surf.blit(glow_s, (sx - glow_r, bot_y - glow_r))

            # === HIỆU ỨNG LÓE SÁNG NÒNG SÚNG MƯỢT MÀ ĐẸP MẮT (MUZZLE FLASH) ===
            if self.muzzle_flash_timer > 0:
                fp = self.muzzle_flash_timer / 0.15  # 1.0 → 0.0 (tiến trình giảm dần)
                # Xác định nòng súng tương ứng theo hướng
                muzzle_x, muzzle_y = sx, sy
                if self.facing == 'right':
                    muzzle_x, muzzle_y = sx + 28, sy - 2
                elif self.facing == 'left':
                    muzzle_x, muzzle_y = sx - 28, sy - 2
                elif self.facing == 'down':
                    muzzle_x, muzzle_y = sx + 12, sy + 22
                elif self.facing == 'up':
                    muzzle_x, muzzle_y = sx - 12, sy - 22

                # --- 1. QUẦNG SÁNG MỜ LỚN (Outer Glow) ---
                glow_r = int(32 * fp)
                if glow_r > 2:
                    glow_s = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
                    pygame.draw.circle(glow_s, (255, 200, 30, int(90 * fp)), (glow_r, glow_r), glow_r)
                    pygame.draw.circle(glow_s, (255, 255, 100, int(60 * fp)), (glow_r, glow_r), glow_r * 2 // 3)
                    surf.blit(glow_s, (muzzle_x - glow_r, muzzle_y - glow_r))

                # --- 2. NGÔI SAO LỬA XOAY (Rotating Fire Star) ---
                fl_size = int(18 * fp)
                pts_outer = []
                pts_inner = []
                rot_offset = (1 - fp) * 4.0  # Xoay theo thời gian
                for i in range(10):
                    ang = self.shoot_angle + i * math.pi / 5 + rot_offset
                    l_out = fl_size * (1.3 if i % 2 == 0 else 0.5)
                    l_in = fl_size * (0.7 if i % 2 == 0 else 0.25)
                    pts_outer.append((muzzle_x + math.cos(ang) * l_out, muzzle_y + math.sin(ang) * l_out))
                    pts_inner.append((muzzle_x + math.cos(ang) * l_in, muzzle_y + math.sin(ang) * l_in))
                if len(pts_outer) > 2:
                    pygame.draw.polygon(surf, (255, 100, 0), pts_outer)       # Lớp cam đỏ ngoài
                    pygame.draw.polygon(surf, (255, 220, 50), pts_inner)      # Lớp vàng sáng trong
                    pygame.draw.circle(surf, (255, 255, 220), (muzzle_x, muzzle_y), max(1, int(6 * fp)))  # Nhân trắng rực

                # --- 3. TIA LỬA PHỤT HƯỚNG BẮN (Directional Flame Jet) ---
                beam_len = int(24 * fp)
                bx = muzzle_x + int(math.cos(self.shoot_angle) * beam_len)
                by = muzzle_y + int(math.sin(self.shoot_angle) * beam_len)
                pygame.draw.line(surf, (255, 220, 50), (muzzle_x, muzzle_y), (bx, by), max(1, int(5 * fp)))
                pygame.draw.line(surf, (255, 255, 220), (muzzle_x, muzzle_y), (bx, by), max(1, int(2 * fp)))
                # Tia lửa phụ hai bên
                perp = self.shoot_angle + math.pi / 2
                for side in [-1, 1]:
                    side_len = int(12 * fp)
                    side_x = muzzle_x + int(math.cos(self.shoot_angle) * 4) + int(math.cos(perp) * side * 5)
                    side_y = muzzle_y + int(math.sin(self.shoot_angle) * 4) + int(math.sin(perp) * side * 5)
                    end_x = side_x + int(math.cos(self.shoot_angle + side * 0.4) * side_len)
                    end_y = side_y + int(math.sin(self.shoot_angle + side * 0.4) * side_len)
                    pygame.draw.line(surf, (255, 160, 30), (side_x, side_y), (end_x, end_y), max(1, int(2 * fp)))

                # --- 4. TIA LỬA NHỎ VĂN NGẪU NHIÊN (Sparks) ---
                if fp > 0.5:
                    for _ in range(4):
                        spark_ang = self.shoot_angle + random.uniform(-0.8, 0.8)
                        spark_dist = random.randint(8, max(8, int(20 * fp)))
                        spk_x = muzzle_x + int(math.cos(spark_ang) * spark_dist)
                        spk_y = muzzle_y + int(math.sin(spark_ang) * spark_dist)
                        spk_r = random.randint(1, 3)
                        pygame.draw.circle(surf, (255, 255, 120), (spk_x, spk_y), spk_r)

                # --- 5. VỎ ĐẠN VĂNG RA (Shell Ejection) ---
                fly_dist = (1.0 - fp) * 22
                shell_perp = self.shoot_angle + math.pi / 2
                shell_x = int(muzzle_x - math.cos(self.shoot_angle) * 8 + math.cos(shell_perp) * fly_dist)
                shell_y = int(muzzle_y - math.sin(self.shoot_angle) * 8 + math.sin(shell_perp) * fly_dist)
                shell_y -= int((1.0 - fp) * 7)  # Bay lên theo parabol
                shell_ang = (1.0 - fp) * math.pi * 5.5
                s_ca, s_sa = math.cos(shell_ang), math.sin(shell_ang)
                slen, swid = 5, 2
                sp1 = (shell_x + s_ca * slen/2 + s_sa * swid/2, shell_y + s_sa * slen/2 - s_ca * swid/2)
                sp2 = (shell_x - s_ca * slen/2 + s_sa * swid/2, shell_y - s_sa * slen/2 - s_ca * swid/2)
                sp3 = (shell_x - s_ca * slen/2 - s_sa * swid/2, shell_y - s_sa * slen/2 + s_ca * swid/2)
                sp4 = (shell_x + s_ca * slen/2 - s_sa * swid/2, shell_y + s_sa * slen/2 + s_ca * swid/2)
                pygame.draw.polygon(surf, (255, 215, 0), [sp1, sp2, sp3, sp4])
                pygame.draw.polygon(surf, (184, 134, 11), [sp1, sp2, sp3, sp4], 1)

        # === VẼ ROBOT KHỔNG LỒ (WHITE_GIANT) 4 HƯỚNG VỚI SÚNG 6 NÒNG ===
        elif self.rtype == 'white_giant' and Robot._giant_sprites_loaded:
            half = self.GIANT_SPRITE_SIZE // 2
            if self.is_moving and self.facing in Robot._giant_walk_frames:
                frames = Robot._giant_walk_frames[self.facing]
                frame = frames[self.anim_frame % len(frames)]
            elif self.facing in Robot._giant_idle_frames:
                frame = Robot._giant_idle_frames[self.facing]
            else:
                frame = Robot._giant_idle_frames.get('down')

            if frame:
                draw_x = sx - half
                draw_y = sy - half - int(self.walk_bob)
                
                if self.recoil_bob > 0.5:
                    recoil_dir = self.shoot_angle + math.pi
                    draw_x += int(math.cos(recoil_dir) * self.recoil_bob)
                    draw_y += int(math.sin(recoil_dir) * self.recoil_bob)

                if self.hit_flash_timer > 0:
                    tinted = frame.copy()
                    red_overlay = pygame.Surface(tinted.get_size(), pygame.SRCALPHA)
                    red_overlay.fill((255, 0, 0, 100))
                    tinted.blit(red_overlay, (0, 0))
                    surf.blit(tinted, (draw_x, draw_y))
                else:
                    surf.blit(frame, (draw_x, draw_y))
                    
            # --- VẼ SÚNG 6 NÒNG CẦM TAY ---
            gun_x, gun_y = sx, sy
            if self.facing == 'right':
                gun_x, gun_y = sx + 25, sy + 10
            elif self.facing == 'left':
                gun_x, gun_y = sx - 25, sy + 10
            elif self.facing == 'down':
                gun_x, gun_y = sx + 15, sy + 25
            elif self.facing == 'up':
                gun_x, gun_y = sx - 15, sy - 15
                
            gun_angle = self.shoot_angle if self.burst_count > 0 or self.shoot_anim_timer > 0 else (
                0 if self.facing == 'right' else math.pi if self.facing == 'left' else math.pi/2 if self.facing == 'down' else -math.pi/2
            )
            
            # Vẽ khối súng 6 nòng (minigun)
            gun_len = 35
            gun_w = 12
            gun_surf = pygame.Surface((gun_len*2, gun_len*2), pygame.SRCALPHA)
            cx, cy = gun_len, gun_len
            
            # Thân súng
            pygame.draw.rect(gun_surf, (80, 80, 80), (cx - 5, cy - gun_w//2, 15, gun_w))
            pygame.draw.rect(gun_surf, (50, 50, 50), (cx + 10, cy - gun_w//2, gun_len - 15, gun_w))
            # 6 nòng súng (vẽ các đường ngang mỏng)
            for i in range(3):
                y_off = -gun_w//2 + 2 + i*4
                pygame.draw.line(gun_surf, (20, 20, 20), (cx + 10, cy + y_off), (cx + gun_len, cy + y_off), 2)
            
            # Xoay súng
            gun_rot = pygame.transform.rotate(gun_surf, -math.degrees(gun_angle))
            gun_rect = gun_rot.get_rect(center=(gun_x, gun_y))
            surf.blit(gun_rot, gun_rect.topleft)

            # === HIỆU ỨNG LÓE SÁNG NÒNG SÚNG (MUZZLE FLASH) ===
            if self.muzzle_flash_timer > 0:
                fp = self.muzzle_flash_timer / 0.2
                muzzle_x = gun_x + math.cos(gun_angle) * gun_len
                muzzle_y = gun_y + math.sin(gun_angle) * gun_len
                
                # Ánh sáng chớp
                glow_r = int(45 * fp)
                if glow_r > 2:
                    glow_s = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
                    pygame.draw.circle(glow_s, (255, 180, 50, int(100 * fp)), (glow_r, glow_r), glow_r)
                    surf.blit(glow_s, (muzzle_x - glow_r, muzzle_y - glow_r))
                    
                # Tia lửa lớn
                beam_len = int(35 * fp)
                bx = muzzle_x + math.cos(gun_angle) * beam_len
                by = muzzle_y + math.sin(gun_angle) * beam_len
                pygame.draw.line(surf, (255, 255, 100), (muzzle_x, muzzle_y), (bx, by), max(1, int(8 * fp)))
                pygame.draw.line(surf, (255, 255, 255), (muzzle_x, muzzle_y), (bx, by), max(1, int(4 * fp)))
                
                # Sparks
                for _ in range(6):
                    spark_ang = gun_angle + random.uniform(-0.5, 0.5)
                    spark_dist = random.randint(10, max(10, int(30 * fp)))
                    spk_x = muzzle_x + math.cos(spark_ang) * spark_dist
                    spk_y = muzzle_y + math.sin(spark_ang) * spark_dist
                    pygame.draw.circle(surf, (255, 200, 50), (spk_x, spk_y), random.randint(1, 4))
                    
                # Vỏ đạn văng liên tục
                if fp > 0.5:
                    shell_perp = gun_angle - math.pi / 2
                    fly_dist = (1.0 - fp) * 30
                    shell_x = muzzle_x - math.cos(gun_angle)*10 + math.cos(shell_perp)*fly_dist
                    shell_y = muzzle_y - math.sin(gun_angle)*10 + math.sin(shell_perp)*fly_dist
                    pygame.draw.circle(surf, (255, 215, 0), (int(shell_x), int(shell_y)), 3)

        else:
            # Fallback: Vẽ robot thô cho các loại khác
            pygame.draw.circle(surf, self.color, (sx, sy), r)
            pygame.draw.circle(surf, (min(255, self.color[0]+40), min(255, self.color[1]+40), min(255, self.color[2]+40)), (sx, sy), r, 2)
            pygame.draw.circle(surf, RED, (sx - 3, sy - 3), 3)
            pygame.draw.circle(surf, RED, (sx + 3, sy - 3), 3)
            pygame.draw.circle(surf, (255, 100, 100), (sx - 3, sy - 3), 1)
            pygame.draw.circle(surf, (255, 100, 100), (sx + 3, sy - 3), 1)
            pygame.draw.line(surf, self.color, (sx, sy - r), (sx, sy - r - 6), 2)
            pygame.draw.circle(surf, RED, (sx, sy - r - 6), 2)
            if self.rtype == 'boss':
                pts = [(sx-10, sy-r-5), (sx-6, sy-r-14), (sx, sy-r-8),
                       (sx+6, sy-r-14), (sx+10, sy-r-5)]
                pygame.draw.polygon(surf, YELLOW, pts)
                pygame.draw.polygon(surf, ORANGE, pts, 2)

        # Thanh máu (dùng chung cho tất cả robot)
        if self.hp < self.max_hp:
            if self.rtype == 'blue':
                bw = self.BLUE_SPRITE_SIZE
                by = sy - (self.BLUE_SPRITE_SIZE // 2 + 8)
            elif self.rtype == 'green':
                bw = self.GREEN_SPRITE_SIZE
                by = sy - (self.GREEN_SPRITE_SIZE // 2 + 8)
            elif self.rtype == 'yellow':
                bw = self.YELLOW_SPRITE_SIZE
                by = sy - (self.YELLOW_SPRITE_SIZE // 2 + 8)
            elif self.rtype == 'white_giant':
                bw = self.GIANT_SPRITE_SIZE
                by = sy - (self.GIANT_SPRITE_SIZE // 2 + 8)
            else:
                bw = r * 2
                by = sy - r - 10
            bh = 4
            bx = sx - bw // 2
            pygame.draw.rect(surf, (60, 0, 0), (bx, by, bw, bh))
            hw = int(bw * self.hp / self.max_hp)
            # Thanh máu đỏ khi tức giận
            hp_color = (255, 50, 50) if self.aggro_timer > 0 else (0, 200, 0)
            pygame.draw.rect(surf, hp_color, (bx, by, hw, bh))


class Bullet:
    def __init__(self, x, y, angle, gun_type='pistol', is_enemy=False, dmg=0):
        self.x, self.y = float(x), float(y)
        self.angle = angle
        self.gun_type = gun_type
        self.is_enemy = is_enemy  # Đạn của robot bắn về phía người chơi
        self.enemy_dmg = dmg      # Sát thương đạn robot
        
        # Thiết lập tốc độ đạn dựa trên loại súng
        if is_enemy:
            speed = BULLET_SPEED * 0.85  # Đạn robot chậm hơn một chút để người chơi né được
        else:
            speed = BULLET_SPEED
            if gun_type == 'sniper':
                speed = BULLET_SPEED * 1.5
            elif gun_type == 'advanced_sniper':
                speed = BULLET_SPEED * 1.8
            elif gun_type == 'smg':
                speed = BULLET_SPEED * 1.1
            
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.alive = True
        
        # Thiết lập kích thước đạn
        if is_enemy:
            self.radius = BULLET_RADIUS + 1
        elif gun_type == 'sniper':
            self.radius = BULLET_RADIUS + 1
        elif gun_type == 'advanced_sniper':
            self.radius = BULLET_RADIUS + 2
        else:
            self.radius = BULLET_RADIUS
            
        self.life = 2.0  # giây tồn tại tối đa
        self.trail = []  # Vệt đuôi đạn cho đạn robot

    def update(self, walls, dt, map_w=MAP_W, map_h=MAP_H):
        self.x += self.vx
        self.y += self.vy
        self.life -= dt
        if self.life <= 0:
            self.alive = False
            return
        # Va chạm tường
        r = self.radius
        rect = pygame.Rect(self.x - r, self.y - r, r * 2, r * 2)
        for w in walls:
            if rect.colliderect(w):
                self.alive = False
                return
        # Ra ngoài map
        if self.x < 0 or self.x > map_w or self.y < 0 or self.y > map_h:
            self.alive = False

    def draw(self, surf, cam_x, cam_y):
        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y)
        
        # === ĐẠN ROBOT (đỏ cam phát sáng + vệt đuôi) ===
        if self.is_enemy:
            # Vệt đuôi đạn phát sáng mờ dần
            trail_len = 12
            for i in range(trail_len):
                t = i / trail_len
                tx = sx - int(math.cos(self.angle) * i * 2)
                ty = sy - int(math.sin(self.angle) * i * 2)
                alpha = int(180 * (1.0 - t))
                tr_r = max(1, int((self.radius + 1) * (1.0 - t * 0.6)))
                trail_s = pygame.Surface((tr_r * 2 + 2, tr_r * 2 + 2), pygame.SRCALPHA)
                pygame.draw.circle(trail_s, (255, 60, 20, alpha), (tr_r + 1, tr_r + 1), tr_r)
                surf.blit(trail_s, (tx - tr_r - 1, ty - tr_r - 1))
            # Quầng sáng cam xung quanh đạn
            glow_s = pygame.Surface((18, 18), pygame.SRCALPHA)
            pygame.draw.circle(glow_s, (255, 100, 30, 90), (9, 9), 8)
            surf.blit(glow_s, (sx - 9, sy - 9))
            # Viên đạn cam đỏ rực rỡ
            pygame.draw.circle(surf, (255, 80, 20), (sx, sy), self.radius + 1)
            pygame.draw.circle(surf, (255, 200, 80), (sx, sy), self.radius)
            pygame.draw.circle(surf, (255, 255, 200), (sx, sy), max(1, self.radius - 1))
            return

        if self.gun_type == 'sniper':
            # Vẽ tia năng lượng laser xanh neon dài tuyệt đẹp
            ex = sx - int(math.cos(self.angle) * 16)
            ey = sy - int(math.sin(self.angle) * 16)
            pygame.draw.line(surf, (0, 200, 255), (sx, sy), (ex, ey), 4)
            pygame.draw.line(surf, WHITE, (sx, sy), (ex, ey), 1)
        elif self.gun_type == 'advanced_sniper':
            # Vẽ tia năng lượng laser xanh lá cây dạ quang dày siêu đẹp
            ex = sx - int(math.cos(self.angle) * 22)
            ey = sy - int(math.sin(self.angle) * 22)
            pygame.draw.line(surf, (0, 255, 100), (sx, sy), (ex, ey), 6)
            pygame.draw.line(surf, WHITE, (sx, sy), (ex, ey), 2)
        elif self.gun_type == 'smg':
            pygame.draw.circle(surf, (255, 100, 255), (sx, sy), self.radius + 1)
            pygame.draw.circle(surf, WHITE, (sx, sy), self.radius)
        else:
            pygame.draw.circle(surf, (255, 255, 100), (sx, sy), self.radius + 1)
            pygame.draw.circle(surf, (255, 200, 50), (sx, sy), self.radius)


class Item:
    def __init__(self, x, y, itype=None):
        if itype is None:
            itype = random.choice(list(ITEM_TYPES.keys()))
        self.x, self.y = float(x), float(y)
        self.itype = itype
        cfg = ITEM_TYPES[itype]
        self.color = cfg['color']
        self.text = cfg['text']
        self.effect = cfg['effect']
        self.value = cfg['value']
        self.alive = True
        self.radius = 14
        self.bob = random.uniform(0, math.pi * 2)

    def update(self, dt):
        self.bob += dt * 3

    def draw(self, surf, cam_x, cam_y):
        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y + math.sin(self.bob) * 3)
        
        # 1. Pulsing Glow effect
        glow_size = int(self.radius * 2.0 + math.sin(self.bob * 2.5) * 4)
        glow = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*self.color, 90 + int(math.sin(self.bob * 2.5) * 40)), (glow_size, glow_size), glow_size)
        surf.blit(glow, (sx - glow_size, sy - glow_size))
        
        # 2. Outer border ring & Inner high-contrast circle
        pygame.draw.circle(surf, self.color, (sx, sy), self.radius + 2, 2)
        pygame.draw.circle(surf, WHITE, (sx, sy), self.radius)
        
        # 3. Custom beautiful icons inside the white circle
        if self.itype == 'battery':
            # Battery: Green cylinder + Metal cap + Lightning bolt
            pygame.draw.rect(surf, (0, 180, 0), (sx - 5, sy - 5, 10, 11), border_radius=1)
            pygame.draw.rect(surf, (120, 120, 120), (sx - 2, sy - 7, 4, 2))
            # Lightning bolt
            pygame.draw.line(surf, WHITE, (sx + 1, sy - 3), (sx - 2, sy), 2)
            pygame.draw.line(surf, WHITE, (sx - 2, sy), (sx + 2, sy + 3), 2)
            
        elif self.itype == 'medkit':
            # Medkit: Bold red cross
            pygame.draw.rect(surf, (220, 40, 40), (sx - 2, sy - 7, 4, 14))
            pygame.draw.rect(surf, (220, 40, 40), (sx - 7, sy - 2, 14, 4))
            
        elif self.itype == 'bulb':
            # Bulb: Bright golden bulb glass + metallic socket base
            pygame.draw.circle(surf, (255, 215, 0), (sx, sy - 2), 6)
            pygame.draw.rect(surf, (120, 120, 120), (sx - 3, sy + 3, 6, 4))
            # Glowing core filament
            pygame.draw.circle(surf, WHITE, (sx, sy - 2), 2, 1)
            
        elif self.itype == 'shoes':
            # Shoes: Blue swift arrowheads >>
            pygame.draw.polygon(surf, (0, 180, 255), [(sx - 6, sy - 6), (sx, sy), (sx - 6, sy + 6)])
            pygame.draw.polygon(surf, (0, 180, 255), [(sx, sy - 6), (sx + 6, sy), (sx, sy + 6)])
            
        elif self.itype == 'magnet':
            # Magnet: Red horseshoe + Silver poles
            pygame.draw.arc(surf, (200, 30, 30), (sx - 5, sy - 5, 10, 10), math.pi, 0, 3)
            pygame.draw.line(surf, (200, 30, 30), (sx - 5, sy), (sx - 5, sy - 3), 3)
            pygame.draw.line(surf, (200, 30, 30), (sx + 4, sy), (sx + 4, sy - 3), 3)
            # Metallic poles
            pygame.draw.rect(surf, (150, 150, 150), (sx - 6, sy - 6, 3, 2))
            pygame.draw.rect(surf, (150, 150, 150), (sx + 3, sy - 6, 3, 2))
            
        elif self.itype == 'wave':
            # Wave: Concentric expanding blue ring waves
            pygame.draw.circle(surf, (0, 100, 255), (sx, sy), 7, 2)
            pygame.draw.circle(surf, (0, 191, 255), (sx, sy), 4, 1)
            
        elif self.itype == 'ammo':
            # Ammo: Two beautiful gold bullets side by side
            # Bullet 1
            pygame.draw.rect(surf, (218, 165, 32), (sx - 4, sy - 2, 3, 7), border_radius=1)
            pygame.draw.polygon(surf, (255, 215, 0), [(sx - 4, sy - 2), (sx - 2, sy - 6), (sx - 1, sy - 2)])
            # Bullet 2
            pygame.draw.rect(surf, (218, 165, 32), (sx + 1, sy - 2, 3, 7), border_radius=1)
            pygame.draw.polygon(surf, (255, 215, 0), [(sx + 1, sy - 2), (sx + 3, sy - 6), (sx + 4, sy - 2)])
            
        # 4. Text Label drawn directly below the item (so it doesn't overlap the custom icon)
        font = _get_font(12)
        txt = font.render(self.text, True, self.color)
        surf.blit(txt, (sx - txt.get_width() // 2, sy + self.radius + 3))

    def apply(self, player):
        if self.effect == 'energy':
            player.energy = min(player.max_energy, player.energy + self.value)
        elif self.effect == 'hp':
            player.hp = min(player.max_hp, player.hp + self.value)
        elif self.effect == 'speed':
            player.speed_boost_timer = self.value
        elif self.effect == 'magnet':
            return 'magnet'
        elif self.effect == 'wave':
            return 'wave'
        elif self.effect == 'ammo':
            player.ammo_reserve = min(player.max_ammo_reserve, player.ammo_reserve + self.value)
        return self.effect


class Particle:
    def __init__(self, x, y, color, vx=None, vy=None, life=0.5, size=3):
        self.x, self.y = float(x), float(y)
        self.vx = vx if vx else random.uniform(-3, 3)
        self.vy = vy if vy else random.uniform(-3, 3)
        self.life = life
        self.max_life = life
        self.color = color
        self.size = size
        self.alive = True

    def update(self, dt):
        self.x += self.vx
        self.y += self.vy
        self.vx *= 0.95
        self.vy *= 0.95
        self.life -= dt
        if self.life <= 0:
            self.alive = False

    def draw(self, surf, cam_x, cam_y):
        alpha = max(0, self.life / self.max_life)
        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y)
        sz = max(1, int(self.size * alpha))
        c = (min(255, int(self.color[0] * alpha + 50)),
             min(255, int(self.color[1] * alpha + 50)),
             min(255, int(self.color[2] * alpha + 50)))
        pygame.draw.circle(surf, c, (sx, sy), sz)


class PlantedLight:
    def __init__(self, x, y):
        self.x, self.y = float(x), float(y)
        self.timer = PLANTED_LIGHT_DURATION
        self.radius = PLANTED_LIGHT_RADIUS
        self.alive = True

    def update(self, dt):
        self.timer -= dt
        if self.timer <= 0:
            self.alive = False

    def draw(self, surf, cam_x, cam_y):
        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y)
        # Glow effect
        for r_off in range(3):
            alpha = int(40 - r_off * 12)
            glow = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow, (255, 255, 150, alpha),
                             (self.radius, self.radius), self.radius - r_off * 10)
            surf.blit(glow, (sx - self.radius, sy - self.radius))
        # Trụ đèn
        pygame.draw.rect(surf, DARK_GRAY, (sx - 3, sy - 8, 6, 16))
        pygame.draw.circle(surf, YELLOW, (sx, sy - 8), 5)
