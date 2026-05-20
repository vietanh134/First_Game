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

            # Tạo thêm các frame cho khổng lồ xanh (white_giant) bằng cách scale lên từ robot thường
            for d in ['up', 'down', 'right', 'left']:
                cls._giant_walk_frames[d] = [pygame.transform.smoothscale(f, (cls.GIANT_SPRITE_SIZE, cls.GIANT_SPRITE_SIZE)) for f in cls._green_walk_frames[d]]
                cls._giant_idle_frames[d] = cls._giant_walk_frames[d][0]

            cls._green_sprites_loaded = True
            cls._giant_sprites_loaded = True
        except Exception as e:
            print(f"[WARN] Không load được sprite robot xanh lá: {e}")
            cls._green_sprites_loaded = False
            cls._giant_sprites_loaded = False

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

        # Load sprites tương ứng
        if self.rtype == 'blue':
            Robot._load_blue_sprites()
        elif self.rtype in ['green', 'white_giant']:
            Robot._load_green_sprites()
        elif self.rtype == 'yellow':
            Robot._load_yellow_sprites()

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
            elif dist < chase_range:
                mx = math.cos(angle_to_player) * chase_speed
                my = math.sin(angle_to_player) * chase_speed
                nx, ny = self.x + mx, self.y + my
                if not self._hit_wall(nx, self.y, walls): self.x = nx
                if not self._hit_wall(self.x, ny, walls): self.y = ny
            else:
                self._wander(walls, dt)

        elif self.rtype in ['white', 'boss', 'white_giant']:
            if dist < 350:
                mx = math.cos(angle_to_player) * self.speed
                my = math.sin(angle_to_player) * self.speed
                nx, ny = self.x + mx, self.y + my
                if not self._hit_wall(nx, self.y, walls): self.x = nx
                if not self._hit_wall(self.x, ny, walls): self.y = ny
            else:
                self._wander(walls, dt)

        elif self.rtype == 'yellow':
            # === TACTICAL AI: Robot vàng - mạnh, strafe + burst 4 viên ===
            self.lightning_timer -= dt
            if self.lightning_timer <= 0:
                self.lightning_timer = random.uniform(0.6, 1.8)  # Tia sét nhấp nháy
            self.lightning_phase += dt * 8.0

            if dist < 550:
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
                        sx_m += math.cos(angle_to_player) * self.speed * 0.5
                        sy_m += math.sin(angle_to_player) * self.speed * 0.5
                    nx, ny = self.x + sx_m, self.y + sy_m
                    if not self._hit_wall(nx, self.y, walls): self.x = nx
                    if not self._hit_wall(self.x, ny, walls): self.y = ny
                elif dist > 280:
                    chase_x = math.cos(angle_to_player) * self.speed * 0.9
                    chase_y = math.sin(angle_to_player) * self.speed * 0.9
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
            if dist < 500:
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
                        sx_m += math.cos(angle_to_player) * self.speed * 0.4
                        sy_m += math.sin(angle_to_player) * self.speed * 0.4
                    nx, ny = self.x + sx_m, self.y + sy_m
                    if not self._hit_wall(nx, self.y, walls): self.x = nx
                    if not self._hit_wall(self.x, ny, walls): self.y = ny
                elif dist > 260:
                    # Tiến về phía player kết hợp strafe nhẹ
                    chase_x = math.cos(angle_to_player) * self.speed * 0.85
                    chase_y = math.sin(angle_to_player) * self.speed * 0.85
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
            if abs(dx_moved) > abs(dy_moved):
                self.facing = 'right' if dx_moved > 0 else 'left'
            else:
                self.facing = 'down' if dy_moved > 0 else 'up'
        else:
            self.is_moving = False
            # Khi robot xanh lá hoặc vàng đứng yên nhưng đang nhắm/bắn → cập nhật facing theo góc bắn
            if self.rtype in ['green', 'yellow'] and dist < 500:
                aim_deg = math.degrees(angle_to_player) % 360
                if 45 <= aim_deg < 135:
                    self.facing = 'down'
                elif 135 <= aim_deg < 225:
                    self.facing = 'left'
                elif 225 <= aim_deg < 315:
                    self.facing = 'up'
                else:
                    self.facing = 'right'

        # Giảm shoot_anim_timer
        if self.rtype in ['green', 'yellow'] and self.shoot_anim_timer > 0:
            self.shoot_anim_timer -= dt

        # Cập nhật frame animation
        # Robot xanh lá và vàng: animate cả khi bắn (shoot_anim_timer > 0)
        is_animating = self.is_moving or (self.rtype in ['green', 'yellow'] and self.shoot_anim_timer > 0)
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
        # Robot xanh bị bắn → tức giận đuổi theo đánh trả!
        if self.rtype == 'blue' and self.hp > 0:
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
                        spark_dist = random.randint(8, int(18 * fp))
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
                        spark_dist = random.randint(8, int(20 * fp))
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

        # === VẼ ROBOT KHỔNG LỒ XANH (WHITE_GIANT) BẰNG SPRITE ANIMATION CỠ LỚN ===
        elif self.rtype == 'white_giant' and Robot._giant_sprites_loaded:
            half = self.GIANT_SPRITE_SIZE // 2
            # Chọn frame phù hợp
            if self.is_moving and self.facing in Robot._giant_walk_frames:
                frames = Robot._giant_walk_frames[self.facing]
                frame = frames[self.anim_frame % len(frames)]
            elif self.facing in Robot._giant_idle_frames:
                frame = Robot._giant_idle_frames[self.facing]
            else:
                frame = Robot._giant_idle_frames.get('down')

            if frame:
                # Tính vị trí vẽ với hiệu ứng nhún (walk bob)
                draw_x = sx - half
                draw_y = sy - half - int(self.walk_bob)
                
                # Nhấp nháy đỏ khi bị trúng đạn
                if self.hit_flash_timer > 0:
                    tinted = frame.copy()
                    red_overlay = pygame.Surface(tinted.get_size(), pygame.SRCALPHA)
                    red_overlay.fill((255, 0, 0, 100))
                    tinted.blit(red_overlay, (0, 0))
                    surf.blit(tinted, (draw_x, draw_y))
                else:
                    surf.blit(frame, (draw_x, draw_y))

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


