"""Level generation: walls, obstacles, items, robots spawn — Enhanced visuals"""
import pygame, random, math
from constants import *
from entities import Robot, Item

class Level:
    def __init__(self, level_num):
        self.num = level_num  # 0-indexed
        self.name = LEVEL_NAMES[level_num]
        self.bg_color = LEVEL_BG_COLORS[level_num]
        self.wall_color = LEVEL_WALL_COLORS[level_num]
        self.walls = []
        self.decorations = []  # (rect, color)
        self.detail_decos = []  # Chi tiết trang trí không chắn đường: (type, x, y, data)
        self.robots = []
        self.items = []
        self.ambient_lights = []  # (x, y, radius) - điểm sáng cố định
        self.map_w = LEVEL_MAP_SIZES[level_num][0]
        self.map_h = LEVEL_MAP_SIZES[level_num][1]
        self._bg_cache = None  # Pre-rendered background surface
        self._generate()
        self._build_bg_cache()  # Pre-render toàn bộ nền + decorations

    # ─── PRE-RENDER CACHE ────────────────────────────────────────────
    def _build_bg_cache(self):
        """Pre-render toàn bộ background + decorations + details vào 1 surface lớn"""
        self._bg_cache = pygame.Surface((self.map_w, self.map_h))
        self._bg_cache.fill(self.bg_color)

        # Vẽ ground pattern theo chủ đề
        self._draw_ground_pattern(self._bg_cache)

        # Vẽ bóng đổ cho tường (offset 4px xuống-phải)
        shadow_color = (max(0, self.bg_color[0]-25), max(0, self.bg_color[1]-25), max(0, self.bg_color[2]-25))
        for w in self.walls:
            shadow = pygame.Rect(w.x + 4, w.y + 4, w.w, w.h)
            pygame.draw.rect(self._bg_cache, shadow_color, shadow)

        # Vẽ decorations (tòa nhà, cây, đá...) lên cache
        for rect, color in self.decorations:
            pygame.draw.rect(self._bg_cache, color, rect)
            # Viền sáng hơn
            border_c = (min(255, color[0]+25), min(255, color[1]+25), min(255, color[2]+25))
            pygame.draw.rect(self._bg_cache, border_c, rect, 1)

        # Vẽ chi tiết trang trí (không chắn đường)
        self._draw_detail_decos(self._bg_cache)

        # Vẽ tường lên cache với texture
        self._draw_walls_textured(self._bg_cache)

    def _draw_ground_pattern(self, surf):
        """Vẽ texture nền theo từng chủ đề màn"""
        random.seed(self.num * 9999 + 77)  # Seed riêng cho ground pattern

        if self.num == 0:  # Thành phố — vỉa hè, vạch đường
            self._ground_city(surf)
        elif self.num == 1:  # Rừng — cỏ, lá rụng
            self._ground_forest(surf)
        elif self.num == 2:  # Sa mạc — cát, vết nứt
            self._ground_desert(surf)
        elif self.num == 3:  # Nghĩa địa — đất bẩn, rêu
            self._ground_graveyard(surf)
        elif self.num == 4:  # Hầm băng — sàn băng, vết nứt
            self._ground_ice(surf)
        elif self.num == 5:  # Pháo đài — sàn kim loại, rãnh
            self._ground_fortress(surf)

    # ─── GROUND TEXTURES ─────────────────────────────────────────────
    def _ground_city(self, surf):
        """Nền thành phố: gạch vỉa hè + đường nhựa"""
        tile_size = 40
        for x in range(0, self.map_w, tile_size):
            for y in range(0, self.map_h, tile_size):
                # Gạch vỉa hè sáng tối xen kẽ
                shade = random.randint(-5, 5)
                c = (45 + shade, 45 + shade, 55 + shade)
                pygame.draw.rect(surf, c, (x, y, tile_size, tile_size))
                # Viền gạch
                pygame.draw.rect(surf, (38, 38, 48), (x, y, tile_size, tile_size), 1)

        # Vạch đường ngang
        road_y_positions = [350, 750]
        for ry in road_y_positions:
            if ry < self.map_h - 40:
                # Đường nhựa đen
                pygame.draw.rect(surf, (30, 30, 35), (20, ry, self.map_w - 40, 60))
                # Vạch kẻ đứt trắng giữa đường
                for dx in range(30, self.map_w - 30, 50):
                    pygame.draw.rect(surf, (180, 180, 150), (dx, ry + 27, 25, 6))

        # Vết nứt ngẫu nhiên trên mặt đường
        for _ in range(15):
            cx = random.randint(30, self.map_w - 30)
            cy = random.randint(30, self.map_h - 30)
            for seg in range(random.randint(3, 6)):
                ex = cx + random.randint(-20, 20)
                ey = cy + random.randint(-15, 15)
                pygame.draw.line(surf, (35, 35, 42), (cx, cy), (ex, ey), 1)
                cx, cy = ex, ey

        # Vệt bẩn / vũng nước nhỏ
        for _ in range(8):
            px = random.randint(40, self.map_w - 40)
            py = random.randint(40, self.map_h - 40)
            pr = random.randint(8, 18)
            puddle_surf = pygame.Surface((pr*2, pr*2), pygame.SRCALPHA)
            pygame.draw.ellipse(puddle_surf, (30, 35, 50, 80), (0, 0, pr*2, pr*2))
            surf.blit(puddle_surf, (px - pr, py - pr))

    def _ground_forest(self, surf):
        """Nền rừng: đất, cỏ rải rác, lá rụng"""
        # Texture đất nâu xanh
        for x in range(0, self.map_w, 8):
            for y in range(0, self.map_h, 8):
                shade = random.randint(-4, 4)
                c = (15 + shade, 35 + shade, 20 + shade)
                pygame.draw.rect(surf, c, (x, y, 8, 8))

        # Cụm cỏ nhỏ rải rác
        for _ in range(80):
            gx = random.randint(25, self.map_w - 25)
            gy = random.randint(25, self.map_h - 25)
            for blade in range(random.randint(3, 6)):
                bx = gx + random.randint(-5, 5)
                by = gy
                tip_x = bx + random.randint(-3, 3)
                tip_y = by - random.randint(5, 12)
                green = random.randint(50, 100)
                pygame.draw.line(surf, (10, green, 15), (bx, by), (tip_x, tip_y), 1)

        # Lá rụng
        for _ in range(40):
            lx = random.randint(25, self.map_w - 25)
            ly = random.randint(25, self.map_h - 25)
            lc = random.choice([
                (80, 50, 20), (100, 60, 15), (60, 80, 20), (90, 70, 10), (50, 70, 25)
            ])
            ls = random.randint(2, 4)
            pygame.draw.ellipse(surf, lc, (lx, ly, ls * 2, ls))

        # Rễ cây lộ thiên
        for _ in range(6):
            rx = random.randint(60, self.map_w - 60)
            ry = random.randint(60, self.map_h - 60)
            for seg in range(random.randint(4, 8)):
                ex = rx + random.randint(-15, 15)
                ey = ry + random.randint(-10, 10)
                pygame.draw.line(surf, (40, 25, 15), (rx, ry), (ex, ey), 2)
                rx, ry = ex, ey

    def _ground_desert(self, surf):
        """Nền sa mạc: cát nhấp nhô, vết nứt khô"""
        # Cát nhiều sắc độ
        for x in range(0, self.map_w, 12):
            for y in range(0, self.map_h, 12):
                shade = random.randint(-8, 8)
                c = (160 + shade, 140 + shade, 90 + shade)
                pygame.draw.rect(surf, c, (x, y, 12, 12))

        # Gợn cát (dune ripples)
        for _ in range(20):
            sx = random.randint(0, self.map_w)
            sy = random.randint(0, self.map_h)
            length = random.randint(60, 200)
            for i in range(length):
                px = sx + i
                py = sy + int(math.sin(i * 0.15) * 3)
                if 0 <= px < self.map_w and 0 <= py < self.map_h:
                    pygame.draw.circle(surf, (170, 150, 100), (px, py), 1)

        # Vết nứt khô trên cát
        for _ in range(12):
            cx = random.randint(40, self.map_w - 40)
            cy = random.randint(40, self.map_h - 40)
            for seg in range(random.randint(5, 10)):
                ex = cx + random.randint(-25, 25)
                ey = cy + random.randint(-20, 20)
                pygame.draw.line(surf, (130, 110, 65), (cx, cy), (ex, ey), 1)
                # Nhánh nhỏ
                if random.random() < 0.4:
                    bx = (cx + ex) // 2 + random.randint(-10, 10)
                    by = (cy + ey) // 2 + random.randint(-8, 8)
                    pygame.draw.line(surf, (125, 105, 60), ((cx+ex)//2, (cy+ey)//2), (bx, by), 1)
                cx, cy = ex, ey

    def _ground_graveyard(self, surf):
        """Nền nghĩa địa: đất tối, rêu, vệt máu cũ"""
        for x in range(0, self.map_w, 10):
            for y in range(0, self.map_h, 10):
                shade = random.randint(-5, 5)
                c = (50 + shade, 50 + shade, 55 + shade)
                pygame.draw.rect(surf, c, (x, y, 10, 10))

        # Vệt rêu xanh đậm
        for _ in range(25):
            mx = random.randint(30, self.map_w - 30)
            my = random.randint(30, self.map_h - 30)
            ms = random.randint(10, 25)
            moss_s = pygame.Surface((ms, ms), pygame.SRCALPHA)
            pygame.draw.ellipse(moss_s, (30, 55, 30, 60), (0, 0, ms, ms))
            surf.blit(moss_s, (mx, my))

        # Vết bẩn tối
        for _ in range(15):
            dx = random.randint(30, self.map_w - 30)
            dy = random.randint(30, self.map_h - 30)
            dr = random.randint(5, 12)
            dark_s = pygame.Surface((dr*2, dr*2), pygame.SRCALPHA)
            pygame.draw.ellipse(dark_s, (35, 30, 30, 50), (0, 0, dr*2, dr*2))
            surf.blit(dark_s, (dx - dr, dy - dr))

    def _ground_ice(self, surf):
        """Nền hầm băng: sàn băng sáng, vết nứt, mảnh băng"""
        for x in range(0, self.map_w, 15):
            for y in range(0, self.map_h, 15):
                shade = random.randint(-6, 6)
                c = (180 + shade, 210 + shade, 230 + shade)
                c = tuple(max(0, min(255, v)) for v in c)
                pygame.draw.rect(surf, c, (x, y, 15, 15))
                # Viền nhẹ
                pygame.draw.rect(surf, (170, 200, 220), (x, y, 15, 15), 1)

        # Vết nứt băng
        for _ in range(18):
            cx = random.randint(30, self.map_w - 30)
            cy = random.randint(30, self.map_h - 30)
            for seg in range(random.randint(4, 9)):
                ex = cx + random.randint(-20, 20)
                ey = cy + random.randint(-15, 15)
                pygame.draw.line(surf, (140, 180, 210), (cx, cy), (ex, ey), 1)
                cx, cy = ex, ey

        # Đốm sáng phản chiếu
        for _ in range(12):
            gx = random.randint(20, self.map_w - 20)
            gy = random.randint(20, self.map_h - 20)
            gs = random.randint(3, 8)
            glint_s = pygame.Surface((gs*2, gs*2), pygame.SRCALPHA)
            pygame.draw.ellipse(glint_s, (220, 240, 255, 60), (0, 0, gs*2, gs*2))
            surf.blit(glint_s, (gx, gy))

    def _ground_fortress(self, surf):
        """Nền pháo đài: sàn kim loại, rãnh, đinh tán"""
        tile = 50
        for x in range(0, self.map_w, tile):
            for y in range(0, self.map_h, tile):
                shade = random.randint(-3, 3)
                c = (20 + shade, 20 + shade, 25 + shade)
                pygame.draw.rect(surf, c, (x, y, tile, tile))
                # Viền tấm kim loại
                pygame.draw.rect(surf, (28, 28, 33), (x, y, tile, tile), 1)
                # Đinh tán 4 góc
                for corner in [(x+4, y+4), (x+tile-6, y+4), (x+4, y+tile-6), (x+tile-6, y+tile-6)]:
                    pygame.draw.circle(surf, (35, 35, 40), corner, 2)
                    pygame.draw.circle(surf, (15, 15, 18), corner, 1)

        # Rãnh năng lượng phát sáng chéo
        for i in range(5):
            sx = random.randint(100, self.map_w - 100)
            sy = random.randint(100, self.map_h - 100)
            length = random.randint(80, 200)
            angle = random.choice([0, math.pi/2, math.pi/4, -math.pi/4])
            ex = int(sx + math.cos(angle) * length)
            ey = int(sy + math.sin(angle) * length)
            # Glow
            glow_s = pygame.Surface((abs(ex-sx)+20, abs(ey-sy)+20), pygame.SRCALPHA)
            ox = min(sx, ex) - 10
            oy = min(sy, ey) - 10
            pygame.draw.line(surf, (60, 15, 15), (sx, sy), (ex, ey), 3)
            pygame.draw.line(surf, (120, 30, 20), (sx, sy), (ex, ey), 1)

    # ─── DETAIL DECORATIONS (không chắn đường) ──────────────────────
    def _draw_detail_decos(self, surf):
        """Vẽ các chi tiết trang trí riêng cho từng màn"""
        random.seed(self.num * 5555 + 99)

        if self.num == 0:
            self._details_city(surf)
        elif self.num == 1:
            self._details_forest(surf)
        elif self.num == 2:
            self._details_desert(surf)
        elif self.num == 3:
            self._details_graveyard(surf)
        elif self.num == 4:
            self._details_ice(surf)
        elif self.num == 5:
            self._details_fortress(surf)

    def _details_city(self, surf):
        """Chi tiết thành phố: cửa sổ tòa nhà, cột đèn, xe hỏng, biển báo"""
        # Cửa sổ trên tòa nhà
        for rect, color in self.decorations:
            if rect.w >= 80 and rect.h >= 80:  # Chỉ tòa nhà lớn
                win_w, win_h = 12, 14
                gap_x, gap_y = 20, 22
                for wx in range(rect.x + 10, rect.x + rect.w - win_w - 5, gap_x):
                    for wy in range(rect.y + 10, rect.y + rect.h - win_h - 5, gap_y):
                        # Cửa sổ sáng hoặc tối
                        if random.random() < 0.3:
                            win_c = (180, 170, 80)  # Sáng vàng
                        else:
                            win_c = (40, 40, 50)  # Tối
                        pygame.draw.rect(surf, win_c, (wx, wy, win_w, win_h))
                        pygame.draw.rect(surf, (55, 55, 65), (wx, wy, win_w, win_h), 1)
                        # Khung cửa chữ thập
                        pygame.draw.line(surf, (55, 55, 65), (wx + win_w//2, wy), (wx + win_w//2, wy + win_h), 1)
                        pygame.draw.line(surf, (55, 55, 65), (wx, wy + win_h//2), (wx + win_w, wy + win_h//2), 1)

        # Cột đèn
        lamp_positions = [(250, 380), (550, 380), (850, 380)]
        for lx, ly in lamp_positions:
            if lx < self.map_w - 20 and ly < self.map_h - 20:
                # Cột
                pygame.draw.rect(surf, (50, 50, 55), (lx, ly - 40, 4, 50))
                # Đèn trên đầu
                pygame.draw.circle(surf, (100, 90, 50), (lx + 2, ly - 42), 6)
                pygame.draw.circle(surf, (70, 65, 35), (lx + 2, ly - 42), 6, 1)
                # Hào quang nhẹ
                glow = pygame.Surface((30, 30), pygame.SRCALPHA)
                pygame.draw.circle(glow, (100, 90, 50, 25), (15, 15), 15)
                surf.blit(glow, (lx - 13, ly - 57))

        # Xe hơi hỏng (vài chiếc)
        car_positions = [(300, 430), (700, 250)]
        for cx, cy in car_positions:
            if cx < self.map_w - 50 and cy < self.map_h - 30:
                # Thân xe
                pygame.draw.rect(surf, (55, 30, 30), (cx, cy, 45, 22))
                pygame.draw.rect(surf, (45, 25, 25), (cx + 5, cy - 10, 35, 12))
                # Bánh xe
                pygame.draw.circle(surf, (25, 25, 25), (cx + 10, cy + 22), 5)
                pygame.draw.circle(surf, (25, 25, 25), (cx + 35, cy + 22), 5)
                # Cửa kính
                pygame.draw.rect(surf, (40, 50, 60), (cx + 8, cy - 8, 13, 8))
                pygame.draw.rect(surf, (40, 50, 60), (cx + 24, cy - 8, 13, 8))

        # Mảnh vỡ rải rác
        for _ in range(20):
            dx = random.randint(30, self.map_w - 30)
            dy = random.randint(30, self.map_h - 30)
            ds = random.randint(2, 5)
            dc = random.choice([(60,55,50), (70,65,55), (50,50,55)])
            pygame.draw.rect(surf, dc, (dx, dy, ds, ds))

    def _details_forest(self, surf):
        """Chi tiết rừng: tán lá tròn, nấm, đá nhỏ, bông hoa"""
        # Tán lá lớn (hình tròn bên trên gốc cây/wall)
        for rect, color in self.decorations:
            tx = rect.x + rect.w // 2
            ty = rect.y + rect.h // 2
            canopy_r = rect.w + random.randint(10, 25)
            canopy_s = pygame.Surface((canopy_r*2, canopy_r*2), pygame.SRCALPHA)
            # Lớp tán lá
            for layer in range(3):
                lr = canopy_r - layer * 5
                lc = (15 + layer*8, 55 + random.randint(0,20) + layer*10, 15 + layer*5, 120 - layer*20)
                lc = tuple(max(0, min(255, v)) for v in lc)
                ox = random.randint(-5, 5)
                oy = random.randint(-5, 5)
                pygame.draw.circle(canopy_s, lc, (canopy_r + ox, canopy_r + oy), lr)
            surf.blit(canopy_s, (tx - canopy_r, ty - canopy_r - 10))

        # Nấm nhỏ
        for _ in range(12):
            mx = random.randint(40, self.map_w - 40)
            my = random.randint(40, self.map_h - 40)
            # Chân nấm
            pygame.draw.rect(surf, (180, 170, 140), (mx, my, 3, 6))
            # Mũ nấm
            cap_c = random.choice([(180, 50, 40), (200, 80, 30), (220, 200, 60)])
            pygame.draw.ellipse(surf, cap_c, (mx - 3, my - 4, 9, 6))
            # Chấm trắng
            pygame.draw.circle(surf, (240, 240, 230), (mx + 1, my - 2), 1)

        # Đá nhỏ rải rác
        for _ in range(20):
            rx = random.randint(30, self.map_w - 30)
            ry = random.randint(30, self.map_h - 30)
            rw = random.randint(4, 10)
            rh = random.randint(3, 7)
            rc = (60 + random.randint(-10, 10), 55 + random.randint(-10, 10), 50)
            pygame.draw.ellipse(surf, rc, (rx, ry, rw, rh))
            pygame.draw.ellipse(surf, (rc[0]+15, rc[1]+15, rc[2]+10), (rx, ry, rw, rh), 1)

        # Hoa dại nhỏ
        for _ in range(10):
            fx = random.randint(30, self.map_w - 30)
            fy = random.randint(30, self.map_h - 30)
            fc = random.choice([(220, 180, 50), (200, 100, 150), (150, 100, 200), (255, 255, 100)])
            pygame.draw.circle(surf, fc, (fx, fy), 2)
            pygame.draw.circle(surf, (255, 230, 80), (fx, fy), 1)

    def _details_desert(self, surf):
        """Chi tiết sa mạc: xương rồng, hộp sọ, bụi cỏ khô"""
        # Xương rồng
        for _ in range(8):
            cx = random.randint(60, self.map_w - 60)
            cy = random.randint(60, self.map_h - 60)
            # Kiểm tra không trùng wall
            test = pygame.Rect(cx - 10, cy - 30, 20, 35)
            if any(test.colliderect(w) for w in self.walls):
                continue
            # Thân chính
            cactus_c = (50, 120, 40)
            pygame.draw.rect(surf, cactus_c, (cx - 4, cy - 25, 8, 30))
            # Nhánh trái
            pygame.draw.rect(surf, cactus_c, (cx - 14, cy - 18, 10, 5))
            pygame.draw.rect(surf, cactus_c, (cx - 14, cy - 23, 5, 10))
            # Nhánh phải
            pygame.draw.rect(surf, cactus_c, (cx + 4, cy - 12, 10, 5))
            pygame.draw.rect(surf, cactus_c, (cx + 9, cy - 20, 5, 13))
            # Viền
            pygame.draw.rect(surf, (40, 100, 30), (cx - 4, cy - 25, 8, 30), 1)

        # Hộp sọ
        for _ in range(4):
            sx = random.randint(50, self.map_w - 50)
            sy = random.randint(50, self.map_h - 50)
            test = pygame.Rect(sx - 6, sy - 6, 12, 12)
            if any(test.colliderect(w) for w in self.walls):
                continue
            # Sọ
            pygame.draw.ellipse(surf, (200, 190, 170), (sx - 6, sy - 7, 12, 10))
            pygame.draw.rect(surf, (200, 190, 170), (sx - 4, sy + 2, 8, 4))
            # Mắt
            pygame.draw.circle(surf, (60, 50, 40), (sx - 2, sy - 3), 2)
            pygame.draw.circle(surf, (60, 50, 40), (sx + 2, sy - 3), 2)
            # Mũi
            pygame.draw.line(surf, (60, 50, 40), (sx, sy), (sx, sy + 1), 1)

        # Bụi cỏ khô
        for _ in range(15):
            gx = random.randint(30, self.map_w - 30)
            gy = random.randint(30, self.map_h - 30)
            for blade in range(random.randint(4, 8)):
                bx = gx + random.randint(-6, 6)
                by = gy
                tip_x = bx + random.randint(-5, 5)
                tip_y = by - random.randint(4, 10)
                pygame.draw.line(surf, (140, 130, 70), (bx, by), (tip_x, tip_y), 1)

    def _details_graveyard(self, surf):
        """Chi tiết nghĩa địa: thập tự giá, hàng rào sắt, cây khô, mạng nhện"""
        # Thập tự giá chi tiết trên bia mộ
        for rect, color in self.decorations:
            if rect.w < 35 and rect.h > 25:  # Bia mộ
                tx = rect.x + rect.w // 2
                ty = rect.y - 5
                # Thập tự
                pygame.draw.rect(surf, (120, 115, 110), (tx - 2, ty - 18, 4, 20))
                pygame.draw.rect(surf, (120, 115, 110), (tx - 7, ty - 14, 14, 3))
                pygame.draw.rect(surf, (100, 95, 90), (tx - 2, ty - 18, 4, 20), 1)
                # Chữ RIP nhỏ trên bia mộ
                font_tiny = pygame.font.SysFont('arial', 8)
                rip_text = font_tiny.render("RIP", True, (140, 135, 130))
                surf.blit(rip_text, (rect.x + rect.w//2 - rip_text.get_width()//2, rect.y + 5))

        # Hàng rào sắt
        fence_segments = [
            (40, 200, 300), (40, 500, 250), (self.map_w - 350, 300, 300)
        ]
        for fx, fy, fw in fence_segments:
            if fx + fw > self.map_w - 30 or fy > self.map_h - 30:
                continue
            # Thanh ngang
            pygame.draw.line(surf, (60, 55, 55), (fx, fy), (fx + fw, fy), 2)
            pygame.draw.line(surf, (60, 55, 55), (fx, fy + 15), (fx + fw, fy + 15), 2)
            # Thanh dọc nhọn
            for bar_x in range(fx, fx + fw, 12):
                pygame.draw.line(surf, (65, 60, 60), (bar_x, fy - 5), (bar_x, fy + 20), 1)
                # Đầu nhọn
                pygame.draw.polygon(surf, (70, 65, 65), [
                    (bar_x - 2, fy - 5), (bar_x, fy - 10), (bar_x + 2, fy - 5)
                ])

        # Cây khô (không lá)
        for _ in range(5):
            tx = random.randint(60, self.map_w - 60)
            ty = random.randint(60, self.map_h - 60)
            test = pygame.Rect(tx - 5, ty - 40, 10, 45)
            if any(test.colliderect(w) for w in self.walls):
                continue
            # Thân cây
            trunk_c = (50, 35, 25)
            pygame.draw.line(surf, trunk_c, (tx, ty), (tx, ty - 35), 3)
            # Nhánh
            for _ in range(random.randint(3, 5)):
                by = ty - random.randint(10, 30)
                bdir = random.choice([-1, 1])
                blen = random.randint(8, 20)
                bend_y = by - random.randint(3, 10)
                pygame.draw.line(surf, trunk_c, (tx, by), (tx + bdir * blen, bend_y), 2)
                # Nhánh con
                if random.random() < 0.5:
                    pygame.draw.line(surf, trunk_c, (tx + bdir * blen, bend_y),
                                     (tx + bdir * (blen + random.randint(3, 8)), bend_y - random.randint(2, 6)), 1)

        # Mạng nhện nhỏ (góc các bia mộ)
        for rect, color in self.decorations[:5]:
            if random.random() < 0.4:
                wx = rect.x
                wy = rect.y
                web_c = (100, 100, 105, 60)
                web_s = pygame.Surface((20, 20), pygame.SRCALPHA)
                # Các sợi từ góc
                for angle in range(0, 90, 15):
                    ex = int(math.cos(math.radians(angle)) * 18)
                    ey = int(math.sin(math.radians(angle)) * 18)
                    pygame.draw.line(web_s, web_c, (0, 0), (ex, ey), 1)
                # Sợi ngang
                for r in [6, 12]:
                    pts = []
                    for angle in range(0, 91, 15):
                        px = int(math.cos(math.radians(angle)) * r)
                        py = int(math.sin(math.radians(angle)) * r)
                        pts.append((px, py))
                    if len(pts) > 1:
                        pygame.draw.lines(web_s, web_c, False, pts, 1)
                surf.blit(web_s, (wx - 2, wy - 2))

    def _details_ice(self, surf):
        """Chi tiết hầm băng: tinh thể, cột nhũ băng, tuyết rơi tĩnh"""
        # Tinh thể băng lấp lánh
        for _ in range(15):
            cx = random.randint(40, self.map_w - 40)
            cy = random.randint(40, self.map_h - 40)
            test = pygame.Rect(cx - 8, cy - 8, 16, 16)
            if any(test.colliderect(w) for w in self.walls):
                continue
            size = random.randint(6, 14)
            crystal_s = pygame.Surface((size*2, size*2), pygame.SRCALPHA)
            # Hình kim cương
            points = [
                (size, 0), (size*2, size), (size, size*2), (0, size)
            ]
            pygame.draw.polygon(crystal_s, (140, 200, 240, 100), points)
            pygame.draw.polygon(crystal_s, (180, 220, 255, 150), points, 1)
            # Highlight
            pygame.draw.line(crystal_s, (220, 240, 255, 120), (size, 2), (size + 3, size - 2), 1)
            surf.blit(crystal_s, (cx - size, cy - size))

        # Cột nhũ băng (stalactite) dọc biên trên
        for i in range(0, self.map_w, random.randint(80, 150)):
            sx = i + random.randint(-20, 20)
            if sx < 25 or sx > self.map_w - 25:
                continue
            sh = random.randint(15, 40)
            # Tam giác treo từ trần
            pts = [(sx - 5, 20), (sx + 5, 20), (sx, 20 + sh)]
            pygame.draw.polygon(surf, (170, 205, 225), pts)
            pygame.draw.polygon(surf, (190, 220, 240), pts, 1)

        # Stalactite từ dưới lên (stalagmite)
        for i in range(0, self.map_w, random.randint(100, 200)):
            sx = i + random.randint(-15, 15)
            if sx < 25 or sx > self.map_w - 25:
                continue
            sh = random.randint(12, 30)
            bottom = self.map_h - 20
            pts = [(sx - 4, bottom), (sx + 4, bottom), (sx, bottom - sh)]
            pygame.draw.polygon(surf, (165, 195, 215), pts)
            pygame.draw.polygon(surf, (185, 215, 235), pts, 1)

        # Hạt tuyết tĩnh
        for _ in range(50):
            fx = random.randint(25, self.map_w - 25)
            fy = random.randint(25, self.map_h - 25)
            fs = random.choice([1, 1, 2])
            snow_s = pygame.Surface((fs*2+2, fs*2+2), pygame.SRCALPHA)
            pygame.draw.circle(snow_s, (230, 240, 255, 80), (fs+1, fs+1), fs)
            surf.blit(snow_s, (fx, fy))

    def _details_fortress(self, surf):
        """Chi tiết pháo đài: ống dẫn, panel điều khiển, rãnh năng lượng, dây cáp"""
        # Ống dẫn ngang/dọc
        pipe_h_positions = [(100, 150, 400), (self.map_w - 500, 600, 400),
                            (200, self.map_h - 200, 350)]
        for px, py, pw in pipe_h_positions:
            if px + pw > self.map_w - 30 or py > self.map_h - 30:
                continue
            # Ống chính
            pygame.draw.rect(surf, (45, 45, 50), (px, py, pw, 8))
            pygame.draw.rect(surf, (55, 55, 60), (px, py, pw, 3))
            # Khớp nối
            for jx in range(px, px + pw, 60):
                pygame.draw.rect(surf, (55, 55, 60), (jx, py - 2, 12, 12))
                pygame.draw.rect(surf, (40, 40, 45), (jx, py - 2, 12, 12), 1)

        # Ống dọc
        pipe_v_positions = [(200, 100, 300), (self.map_w - 250, 200, 350)]
        for px, py, ph in pipe_v_positions:
            if py + ph > self.map_h - 30 or px > self.map_w - 30:
                continue
            pygame.draw.rect(surf, (42, 42, 48), (px, py, 8, ph))
            pygame.draw.rect(surf, (52, 52, 58), (px, py, 3, ph))
            for jy in range(py, py + ph, 50):
                pygame.draw.rect(surf, (52, 52, 58), (px - 2, jy, 12, 10))
                pygame.draw.rect(surf, (38, 38, 43), (px - 2, jy, 12, 10), 1)

        # Panel điều khiển
        panel_positions = [(350, 250), (self.map_w - 400, 400), (500, self.map_h - 300)]
        for ppx, ppy in panel_positions:
            if ppx > self.map_w - 60 or ppy > self.map_h - 50:
                continue
            # Hộp panel
            pygame.draw.rect(surf, (35, 35, 40), (ppx, ppy, 50, 35))
            pygame.draw.rect(surf, (50, 50, 55), (ppx, ppy, 50, 35), 1)
            # Màn hình nhỏ
            pygame.draw.rect(surf, (20, 50, 30), (ppx + 5, ppy + 5, 20, 12))
            # Đèn LED
            led_colors = [(0, 200, 0), (200, 50, 0), (0, 100, 200)]
            for i, lc in enumerate(led_colors):
                pygame.draw.circle(surf, lc, (ppx + 35 + i * 6, ppy + 10), 2)
            # Nút bấm
            for i in range(3):
                pygame.draw.rect(surf, (60, 60, 65), (ppx + 5 + i * 15, ppy + 22, 10, 8))

        # Dây cáp lủng lẳng
        for _ in range(6):
            cx = random.randint(100, self.map_w - 100)
            cy = random.randint(100, self.map_h - 100)
            cable_c = random.choice([(80, 30, 30), (30, 30, 80), (80, 80, 30)])
            points = [(cx, cy)]
            for seg in range(random.randint(4, 8)):
                nx = cx + random.randint(-20, 20)
                ny = cy + random.randint(5, 15)
                points.append((nx, ny))
                cx, cy = nx, ny
            if len(points) > 1:
                pygame.draw.lines(surf, cable_c, False, points, 1)

    # ─── TEXTURED WALLS ──────────────────────────────────────────────
    def _draw_walls_textured(self, surf):
        """Vẽ tường với texture pattern"""
        random.seed(self.num * 7777 + 33)

        for w in self.walls:
            # Tường chính
            pygame.draw.rect(surf, self.wall_color, w)

            # Texture pattern theo chủ đề
            if self.num == 0:  # Gạch
                self._wall_brick_texture(surf, w)
            elif self.num == 1:  # Gỗ/vỏ cây
                self._wall_wood_texture(surf, w)
            elif self.num == 2:  # Đá sa mạc
                self._wall_stone_texture(surf, w)
            elif self.num == 3:  # Đá rêu
                self._wall_mossy_texture(surf, w)
            elif self.num == 4:  # Băng
                self._wall_ice_texture(surf, w)
            elif self.num == 5:  # Kim loại
                self._wall_metal_texture(surf, w)

            # Viền highlight trên & trái (3D effect)
            highlight = (min(255, self.wall_color[0]+30), min(255, self.wall_color[1]+30), min(255, self.wall_color[2]+30))
            shadow = (max(0, self.wall_color[0]-20), max(0, self.wall_color[1]-20), max(0, self.wall_color[2]-20))
            pygame.draw.line(surf, highlight, (w.x, w.y), (w.x + w.w, w.y), 1)  # Top
            pygame.draw.line(surf, highlight, (w.x, w.y), (w.x, w.y + w.h), 1)  # Left
            pygame.draw.line(surf, shadow, (w.x, w.y + w.h), (w.x + w.w, w.y + w.h), 1)  # Bottom
            pygame.draw.line(surf, shadow, (w.x + w.w, w.y), (w.x + w.w, w.y + w.h), 1)  # Right

    def _wall_brick_texture(self, surf, w):
        """Texture gạch cho tường thành phố"""
        brick_h = 8
        brick_w = 16
        row = 0
        for y in range(w.y + 1, w.y + w.h - 1, brick_h):
            offset = (brick_w // 2) if row % 2 else 0
            for x in range(w.x + 1 - offset, w.x + w.w, brick_w):
                bx = max(w.x + 1, x)
                bw = min(brick_w, w.x + w.w - 1 - bx)
                bh = min(brick_h - 1, w.y + w.h - 1 - y)
                if bw > 2 and bh > 2:
                    mortar_c = (max(0, self.wall_color[0]-12), max(0, self.wall_color[1]-12), max(0, self.wall_color[2]-12))
                    pygame.draw.rect(surf, mortar_c, (bx, y, bw, bh), 1)
            row += 1

    def _wall_wood_texture(self, surf, w):
        """Texture vân gỗ cho tường rừng"""
        for y in range(w.y + 2, w.y + w.h - 2, 5):
            shade = random.randint(-8, 8)
            c = (max(0, self.wall_color[0] + shade), max(0, self.wall_color[1] + shade), max(0, self.wall_color[2] + shade))
            c = tuple(min(255, v) for v in c)
            pygame.draw.line(surf, c, (w.x + 2, y), (w.x + w.w - 2, y), 1)

    def _wall_stone_texture(self, surf, w):
        """Texture đá thô cho tường sa mạc"""
        for _ in range(max(1, (w.w * w.h) // 200)):
            sx = random.randint(w.x + 2, max(w.x + 3, w.x + w.w - 4))
            sy = random.randint(w.y + 2, max(w.y + 3, w.y + w.h - 4))
            shade = random.randint(-15, 10)
            c = (max(0, min(255, self.wall_color[0] + shade)),
                 max(0, min(255, self.wall_color[1] + shade)),
                 max(0, min(255, self.wall_color[2] + shade)))
            pygame.draw.circle(surf, c, (sx, sy), random.randint(1, 3))

    def _wall_mossy_texture(self, surf, w):
        """Texture rêu cho tường nghĩa địa"""
        # Nền rêu phía dưới
        moss_h = min(w.h // 3, 10)
        if moss_h > 2:
            for x in range(w.x, w.x + w.w, 3):
                mh = random.randint(2, moss_h)
                mc = (30 + random.randint(0, 20), 50 + random.randint(0, 15), 25)
                pygame.draw.rect(surf, mc, (x, w.y + w.h - mh, 3, mh))

    def _wall_ice_texture(self, surf, w):
        """Texture băng cho tường hầm băng"""
        # Đốm sáng phản chiếu
        for _ in range(max(1, (w.w * w.h) // 300)):
            gx = random.randint(w.x + 2, max(w.x + 3, w.x + w.w - 3))
            gy = random.randint(w.y + 2, max(w.y + 3, w.y + w.h - 3))
            glint = pygame.Surface((4, 4), pygame.SRCALPHA)
            pygame.draw.circle(glint, (220, 240, 255, 80), (2, 2), 2)
            surf.blit(glint, (gx, gy))

    def _wall_metal_texture(self, surf, w):
        """Texture kim loại cho tường pháo đài"""
        # Vạch ngang metallic
        for y in range(w.y + 3, w.y + w.h - 2, 8):
            shade = random.choice([-5, 0, 5])
            c = (max(0, min(255, self.wall_color[0] + shade)),
                 max(0, min(255, self.wall_color[1] + shade)),
                 max(0, min(255, self.wall_color[2] + shade)))
            pygame.draw.line(surf, c, (w.x + 2, y), (w.x + w.w - 2, y), 1)
        # Đinh tán
        if w.w > 20 and w.h > 20:
            for corner in [(w.x+6, w.y+6), (w.x+w.w-8, w.y+6),
                           (w.x+6, w.y+w.h-8), (w.x+w.w-8, w.y+w.h-8)]:
                pygame.draw.circle(surf, (55, 55, 60), corner, 3)
                pygame.draw.circle(surf, (35, 35, 38), corner, 2)

    # ─── MAIN GENERATION ─────────────────────────────────────────────
    def _generate(self):
        random.seed(self.num * 1234 + 42)
        # Tường biên
        th = 20
        self.walls.append(pygame.Rect(0, 0, self.map_w, th))
        self.walls.append(pygame.Rect(0, self.map_h - th, self.map_w, th))
        self.walls.append(pygame.Rect(0, 0, th, self.map_h))
        self.walls.append(pygame.Rect(self.map_w - th, 0, th, self.map_h))

        if self.num == 0:
            self._gen_city()
        elif self.num == 1:
            self._gen_forest()
        elif self.num == 2:
            self._gen_desert()
        elif self.num == 3:
            self._gen_graveyard()
        elif self.num == 4:
            self._gen_ice()
        elif self.num == 5:
            self._gen_fortress()

        # Spawn robots
        robot_counts = LEVEL_ROBOTS[self.num]
        for rtype, count in robot_counts.items():
            for _ in range(count):
                for attempt in range(50):
                    x = random.randint(200, self.map_w - 200)
                    y = random.randint(200, self.map_h - 200)
                    # Không spawn quá gần player (player ở 100,100)
                    if math.hypot(x - 100, y - 100) < 300:
                        continue
                    # Không spawn trong tường
                    r = ROBOT_CONFIGS[rtype]['radius']
                    test = pygame.Rect(x - r, y - r, r * 2, r * 2)
                    if not any(test.colliderect(w) for w in self.walls):
                        self.robots.append(Robot(x, y, rtype))
                        break

        # Spawn items ngẫu nhiên (nhiều hơn, ưu tiên năng lượng)
        if self.num == 0:
            num_items = 5 # Giảm vật phẩm màn 1 để tránh bản đồ chật chội
        else:
            num_items = 20 + self.num * 4
        # Danh sách item ưu tiên năng lượng (battery, bulb xuất hiện nhiều hơn)
        weighted_types = ['battery', 'battery', 'battery', 'bulb', 'bulb', 'bulb',
                          'medkit', 'medkit', 'shoes', 'magnet', 'wave']
        for _ in range(num_items):
            for attempt in range(50):
                x = random.randint(60, self.map_w - 60)
                y = random.randint(60, self.map_h - 60)
                test = pygame.Rect(x - 10, y - 10, 20, 20)
                if not any(test.colliderect(w) for w in self.walls):
                    itype = random.choice(weighted_types)
                    self.items.append(Item(x, y, itype))
                    break

    def _add_rect_wall(self, x, y, w, h):
        rect = pygame.Rect(x, y, w, h)
        self.walls.append(rect)
        return rect

    # ─── LEVEL GENERATORS (giữ nguyên layout, thêm decorations) ─────
    def _gen_city(self):
        """Màn 1: Thành phố hoang tàn"""
        # Tòa nhà - thu lại vì map nhỏ (1000x600)
        buildings = [
            (180, 80, 100, 120), (280, 50, 80, 140), (450, 120, 100, 100),
            (650, 60, 90, 130), (150, 300, 120, 80), (400, 350, 100, 110),
            (600, 320, 80, 120), (800, 150, 100, 100), (830, 380, 80, 100),
        ]
        for bx, by, bw, bh in buildings:
            if bx + bw < self.map_w - 20 and by + bh < self.map_h - 20:
                self._add_rect_wall(bx, by, bw, bh)
                self.decorations.append((pygame.Rect(bx, by, bw, bh), (70, 70, 80)))
        # Đèn đường hỏng (ambient lights yếu)
        for i in range(4):
            self.ambient_lights.append((200 + i * 220, 300, 50))

    def _gen_forest(self):
        """Màn 2: Rừng rậm"""
        for _ in range(35):
            x = random.randint(60, self.map_w - 60)
            y = random.randint(60, self.map_h - 60)
            s = random.randint(25, 50)
            self._add_rect_wall(x, y, s, s)
            self.decorations.append((pygame.Rect(x, y, s, s), (20, 60 + random.randint(0, 30), 20)))
        # Ít ambient light
        for i in range(3):
            self.ambient_lights.append((random.randint(200, self.map_w-200), random.randint(200, self.map_h-200), 40))

    def _gen_desert(self):
        """Màn 3: Sa mạc"""
        # Đá lớn
        for _ in range(20):
            x = random.randint(60, self.map_w - 60)
            y = random.randint(60, self.map_h - 60)
            w = random.randint(40, 80)
            h = random.randint(30, 60)
            self._add_rect_wall(x, y, w, h)
            self.decorations.append((pygame.Rect(x, y, w, h), (140 + random.randint(-10, 10), 120, 60)))
        # Nhiều ambient hơn (ban ngày)
        for i in range(8):
            self.ambient_lights.append((random.randint(100, self.map_w-100), random.randint(100, self.map_h-100), 80))

    def _gen_graveyard(self):
        """Màn 4: Nghĩa địa"""
        # Bia mộ
        for _ in range(30):
            x = random.randint(60, self.map_w - 60)
            y = random.randint(60, self.map_h - 60)
            w = random.randint(15, 30)
            h = random.randint(30, 50)
            self._add_rect_wall(x, y, w, h)
            self.decorations.append((pygame.Rect(x, y, w, h), (90, 90, 95)))
        # Rất ít ánh sáng
        self.ambient_lights.append((self.map_w // 2, self.map_h // 2, 30))

    def _gen_ice(self):
        """Màn 5: Hầm băng"""
        # Tảng băng
        for _ in range(25):
            x = random.randint(60, self.map_w - 60)
            y = random.randint(60, self.map_h - 60)
            w = random.randint(30, 70)
            h = random.randint(30, 70)
            self._add_rect_wall(x, y, w, h)
            self.decorations.append((pygame.Rect(x, y, w, h), (160, 200, 220)))
        # Tối om
        pass

    def _gen_fortress(self):
        """Màn 6: Pháo Đài Tận Thế"""
        t = 40
        # Vòng bao bọc bên ngoài (kiểu thành luỹ bằng kim loại)
        self._add_rect_wall(40, 40, self.map_w - 80, t)
        self._add_rect_wall(40, self.map_h - 40 - t, self.map_w - 80, t)
        self._add_rect_wall(40, 80, t, self.map_h - 160)
        self._add_rect_wall(self.map_w - 40 - t, 80, t, self.map_h - 160)
        
        self.decorations.append((pygame.Rect(40, 40, self.map_w-80, t), (60, 60, 65)))
        self.decorations.append((pygame.Rect(40, self.map_h-40-t, self.map_w-80, t), (60, 60, 65)))
        self.decorations.append((pygame.Rect(40, 80, t, self.map_h-160), (60, 60, 65)))
        self.decorations.append((pygame.Rect(self.map_w-40-t, 80, t, self.map_h-160), (60, 60, 65)))

        # Trụ phòng thủ bên trong (Core Pillars) xếp thành hàng
        for x in range(300, self.map_w - 300, 500):
            for y in range(300, self.map_h - 300, 400):
                self._add_rect_wall(x, y, 120, 120)
                self.decorations.append((pygame.Rect(x, y, 120, 120), (35, 35, 40)))
                # Vẽ viền rãnh năng lượng đỏ xung quanh trụ
                self.decorations.append((pygame.Rect(x+10, y+10, 100, 100), (100, 30, 30)))
                # Thêm đèn đỏ ở các trụ
                self.ambient_lights.append((x + 60, y + 60, 90))

        # Lò phản ứng trung tâm (Central Core) cực lớn
        cx, cy = self.map_w // 2, self.map_h // 2
        self._add_rect_wall(cx - 180, cy - 180, 360, 360)
        self.decorations.append((pygame.Rect(cx - 180, cy - 180, 360, 360), (50, 50, 55)))
        # Bề mặt tản nhiệt lõi
        for i in range(5):
            self.decorations.append((pygame.Rect(cx - 150 + i*65, cy - 150, 20, 300), (30, 30, 30)))
        
        # Ánh sáng chói lóa từ Lò phản ứng
        self.ambient_lights.append((cx, cy, 400))
        
        # Vật cản ngẫu nhiên (Barricades) bằng bê tông cốt thép
        for _ in range(25):
            bx = random.randint(120, self.map_w - 120)
            by = random.randint(120, self.map_h - 120)
            # Tránh đặt vật cản quá gần Lò phản ứng hoặc Trụ chính
            if math.hypot(bx - cx, by - cy) < 400:
                continue
            bw = random.choice([150, 40])
            bh = 190 - bw
            self._add_rect_wall(bx, by, bw, bh)
            self.decorations.append((pygame.Rect(bx, by, bw, bh), (80, 80, 85)))

    # ─── DRAW METHODS ────────────────────────────────────────────────
    def draw_bg(self, surf, cam_x, cam_y):
        """Vẽ nền từ cache — chỉ blit phần visible"""
        if self._bg_cache:
            # Nếu kích thước bản đồ nhỏ hơn màn hình, vẽ đè phần thừa màu đen và căn giữa bản đồ
            dest_x = 0
            dest_y = 0
            
            src_x = int(cam_x)
            src_y = int(cam_y)
            
            if self.map_w < WIDTH:
                dest_x = (WIDTH - self.map_w) // 2
                src_x = 0
            else:
                src_x = max(0, min(self.map_w - WIDTH, src_x))
                
            if self.map_h < HEIGHT:
                dest_y = (HEIGHT - self.map_h) // 2
                src_y = 0
            else:
                src_y = max(0, min(self.map_h - HEIGHT, src_y))
                
            src_rect = pygame.Rect(src_x, src_y, WIDTH, HEIGHT)
            
            # Xóa màn hình bằng màu đen trước khi blit bản đồ căn giữa
            surf.fill((0, 0, 0))
            surf.blit(self._bg_cache, (dest_x, dest_y), src_rect)
        else:
            # Fallback nếu cache chưa sẵn sàng
            surf.fill(self.bg_color)
            for rect, color in self.decorations:
                dr = pygame.Rect(rect.x - cam_x, rect.y - cam_y, rect.w, rect.h)
                if dr.right > 0 and dr.left < WIDTH and dr.bottom > 0 and dr.top < HEIGHT:
                    pygame.draw.rect(surf, color, dr)
                    pygame.draw.rect(surf, (min(255, color[0]+20), min(255, color[1]+20), min(255, color[2]+20)), dr, 1)

    def draw_walls(self, surf, cam_x, cam_y):
        """Tường đã được vẽ trong cache, method này giờ không cần làm gì thêm"""
        # Tường đã pre-render trong _bg_cache, không cần vẽ lại
        pass
