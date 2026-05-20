"""Level generation: walls, obstacles, items, robots spawn"""
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
        self.robots = []
        self.items = []
        self.ambient_lights = []  # (x, y, radius) - điểm sáng cố định
        self.map_w = LEVEL_MAP_SIZES[level_num][0]
        self.map_h = LEVEL_MAP_SIZES[level_num][1]
        self._generate()

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

    def _gen_city(self):
        """Màn 1: Thành phố hoang tàn"""
        # Tòa nhà
        buildings = [
            (150, 200, 120, 160), (400, 100, 100, 200), (650, 300, 140, 120),
            (900, 150, 100, 180), (200, 500, 160, 100), (500, 600, 120, 140),
            (800, 500, 100, 160), (1100, 200, 140, 120), (1300, 400, 100, 200),
            (1500, 100, 120, 160), (1700, 300, 140, 100), (1900, 500, 100, 180),
            (350, 900, 120, 120), (700, 800, 100, 100), (1000, 900, 160, 80),
            (1200, 700, 80, 140), (1500, 800, 120, 100), (1800, 900, 100, 120),
            (250, 1200, 140, 100), (600, 1100, 100, 160), (950, 1200, 120, 100),
            (1300, 1100, 100, 140), (1650, 1200, 140, 80), (2000, 1000, 100, 160),
        ]
        for bx, by, bw, bh in buildings:
            self._add_rect_wall(bx, by, bw, bh)
            self.decorations.append((pygame.Rect(bx, by, bw, bh), (70, 70, 80)))
        # Đèn đường hỏng (ambient lights yếu)
        for i in range(6):
            self.ambient_lights.append((300 + i * 350, 400, 50))

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

    def draw_bg(self, surf, cam_x, cam_y):
        """Vẽ nền và trang trí"""
        surf.fill(self.bg_color)
        # Decorations
        for rect, color in self.decorations:
            dr = pygame.Rect(rect.x - cam_x, rect.y - cam_y, rect.w, rect.h)
            if dr.right > 0 and dr.left < WIDTH and dr.bottom > 0 and dr.top < HEIGHT:
                pygame.draw.rect(surf, color, dr)
                # Viền
                pygame.draw.rect(surf, (min(255, color[0]+20), min(255, color[1]+20), min(255, color[2]+20)), dr, 1)

    def draw_walls(self, surf, cam_x, cam_y):
        for w in self.walls:
            dr = pygame.Rect(w.x - cam_x, w.y - cam_y, w.w, w.h)
            if dr.right > 0 and dr.left < WIDTH and dr.bottom > 0 and dr.top < HEIGHT:
                pygame.draw.rect(surf, self.wall_color, dr)
