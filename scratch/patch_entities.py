import re

with open('entities.py', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Remove old giant sprite loading from _load_green_sprites
old_giant_load = """            # Tạo thêm các frame cho khổng lồ xanh (white_giant) bằng cách scale lên từ robot thường
            for d in ['up', 'down', 'right', 'left']:
                cls._giant_walk_frames[d] = [pygame.transform.smoothscale(f, (cls.GIANT_SPRITE_SIZE, cls.GIANT_SPRITE_SIZE)) for f in cls._green_walk_frames[d]]
                cls._giant_idle_frames[d] = cls._giant_walk_frames[d][0]

            cls._green_sprites_loaded = True
            cls._giant_sprites_loaded = True
        except Exception as e:
            print(f"[WARN] Không load được sprite robot xanh lá: {e}")
            cls._green_sprites_loaded = False
            cls._giant_sprites_loaded = False"""
            
new_giant_load = """            cls._green_sprites_loaded = True
        except Exception as e:
            print(f"[WARN] Không load được sprite robot xanh lá: {e}")
            cls._green_sprites_loaded = False"""

code = code.replace(old_giant_load, new_giant_load)

# 2. Add _load_giant_sprites before _load_green_sprites or somewhere after
giant_method = """    @classmethod
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

"""

code = code.replace("    @classmethod\n    def _load_green_sprites(cls):", giant_method + "    @classmethod\n    def _load_green_sprites(cls):")

# 3. Fix __init__ to call _load_giant_sprites
init_call_old = """        elif self.rtype in ['green', 'white_giant']:
            Robot._load_green_sprites()"""
init_call_new = """        elif self.rtype == 'green':
            Robot._load_green_sprites()
        elif self.rtype == 'white_giant':
            Robot._load_giant_sprites()"""
code = code.replace(init_call_old, init_call_new)

# 4. Modify update to handle white_giant AI
ai_old = """        elif self.rtype in ['white', 'boss', 'white_giant']:
            if dist < 350:
                mx = math.cos(angle_to_player) * self.speed
                my = math.sin(angle_to_player) * self.speed
                nx, ny = self.x + mx, self.y + my
                if not self._hit_wall(nx, self.y, walls): self.x = nx
                if not self._hit_wall(self.x, ny, walls): self.y = ny
            else:
                self._wander(walls, dt)"""

ai_new = """        elif self.rtype in ['white', 'boss']:
            if dist < 350:
                mx = math.cos(angle_to_player) * self.speed
                my = math.sin(angle_to_player) * self.speed
                nx, ny = self.x + mx, self.y + my
                if not self._hit_wall(nx, self.y, walls): self.x = nx
                if not self._hit_wall(self.x, ny, walls): self.y = ny
            else:
                self._wander(walls, dt)
                
        elif self.rtype == 'white_giant':
            # Giant AI: Di chuyển 4 hướng chiến thuật, giữ khoảng cách bắn súng 6 nòng
            if dist < 600:
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
                    chase_x = math.cos(angle_to_player) * self.speed * 0.8
                    chase_y = math.sin(angle_to_player) * self.speed * 0.8
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
                    self.burst_timer = 0.15 # Tốc độ xả đạn nhanh giữa các viên"""

code = code.replace(ai_old, ai_new)

# 5. Modify anim state updating
anim_update_old = "is_animating = self.is_moving or (self.rtype in ['green', 'yellow'] and self.shoot_anim_timer > 0)"
anim_update_new = "is_animating = self.is_moving or (self.rtype in ['green', 'yellow', 'white_giant'] and self.shoot_anim_timer > 0)"
code = code.replace(anim_update_old, anim_update_new)

anim_timer_old = "if self.rtype in ['green', 'yellow'] and self.shoot_anim_timer > 0:"
anim_timer_new = "if self.rtype in ['green', 'yellow', 'white_giant'] and self.shoot_anim_timer > 0:"
code = code.replace(anim_timer_old, anim_timer_new)

facing_old = "if self.rtype in ['green', 'yellow'] and dist < 500:"
facing_new = "if self.rtype in ['green', 'yellow', 'white_giant'] and dist < 600:"
code = code.replace(facing_old, facing_new)

anim_frame_old = """                elif self.rtype == 'blue' and Robot._blue_sprites_loaded:
                    frames_dict = Robot._blue_walk_frames
                    if self.facing in frames_dict and frames_dict[self.facing]:
                        max_f = len(frames_dict[self.facing])
                self.anim_frame = (self.anim_frame + 1) % max_f"""

anim_frame_new = """                elif self.rtype == 'blue' and Robot._blue_sprites_loaded:
                    frames_dict = Robot._blue_walk_frames
                    if self.facing in frames_dict and frames_dict[self.facing]:
                        max_f = len(frames_dict[self.facing])
                elif self.rtype == 'white_giant' and Robot._giant_sprites_loaded:
                    frames_dict = Robot._giant_walk_frames
                    if self.facing in frames_dict and frames_dict[self.facing]:
                        max_f = len(frames_dict[self.facing])
                self.anim_frame = (self.anim_frame + 1) % max_f"""
code = code.replace(anim_frame_old, anim_frame_new)

# 6. Modify white_giant drawing logic
draw_giant_old = """        # === VẼ ROBOT KHỔNG LỒ XANH (WHITE_GIANT) BẰNG SPRITE ANIMATION CỠ LỚN ===
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
                    surf.blit(frame, (draw_x, draw_y))"""

draw_giant_new = """        # === VẼ ROBOT KHỔNG LỒ (WHITE_GIANT) 4 HƯỚNG VỚI SÚNG 6 NÒNG ===
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
                    spark_dist = random.randint(10, int(30 * fp))
                    spk_x = muzzle_x + math.cos(spark_ang) * spark_dist
                    spk_y = muzzle_y + math.sin(spark_ang) * spark_dist
                    pygame.draw.circle(surf, (255, 200, 50), (spk_x, spk_y), random.randint(1, 4))
                    
                # Vỏ đạn văng liên tục
                if fp > 0.5:
                    shell_perp = gun_angle - math.pi / 2
                    fly_dist = (1.0 - fp) * 30
                    shell_x = muzzle_x - math.cos(gun_angle)*10 + math.cos(shell_perp)*fly_dist
                    shell_y = muzzle_y - math.sin(gun_angle)*10 + math.sin(shell_perp)*fly_dist
                    pygame.draw.circle(surf, (255, 215, 0), (int(shell_x), int(shell_y)), 3)"""
                    
code = code.replace(draw_giant_old, draw_giant_new)

with open('entities.py', 'w', encoding='utf-8') as f:
    f.write(code)
print("Updated entities.py successfully")
