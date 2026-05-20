"""Constants và cấu hình game Stick Survivor CR7"""
import pygame
import math

# Màn hình
WIDTH, HEIGHT = 1280, 720
FPS = 60
TILE = 40

# Default Map size (pixels) - keep for compatibility if needed
MAP_W, MAP_H = 2400, 1800

# Level map sizes: (width, height)
LEVEL_MAP_SIZES = [
    (1000, 600),   # Màn 1: Nhỏ như game khởi động
    (1280, 900),   # Màn 2: Nhỏ 1/3 map 2 hiện tại (đảm bảo >= màn hình)
    (1600, 1200),  # Màn 3: To hơn map 2 xíu
    (2400, 1800),  # Màn 4: Giữ nguyên
    (2400, 1800),  # Màn 5: Giữ nguyên
    (2400, 1800),  # Màn 6: Giữ nguyên
]

# Màu sắc
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (220, 50, 50)
GREEN = (50, 200, 50)
BLUE = (50, 100, 220)
YELLOW = (255, 220, 50)
CYAN = (50, 220, 220)
ORANGE = (255, 150, 50)
GRAY = (128, 128, 128)
DARK_GRAY = (60, 60, 60)
LIGHT_GRAY = (180, 180, 180)

# Player
PLAYER_SPEED = 5
PLAYER_SPRINT_MULT = 1.5
PLAYER_HP = 300
PLAYER_ENERGY = 100
PLAYER_RADIUS = 14

# Đèn
LIGHT_RANGE = 800
LIGHT_ANGLE = 75  # degrees
LIGHT_DRAIN = 4  # %/s
LIGHT_REGEN = 1.5  # %/s
DARK_RADIUS = 65  # bán kính nhìn khi tắt đèn
PLANTED_LIGHT_DURATION = 10  # seconds
PLANTED_LIGHT_COST = 20
PLANTED_LIGHT_RADIUS = 100
FLASH_COST = 15
SCAN_COST = 10
SCAN_RADIUS = 250
PULSE_COST = 40
PULSE_BLIND_TIME = 3  # seconds

# Đạn
BULLET_SPEED = 8
BULLET_DAMAGE = 25
BULLET_COST = 4
BULLET_RADIUS = 4

# Kiếm
SWORD_DAMAGE = 18
SWORD_RANGE = 45      # pixels - tầm chém
SWORD_ARC = 120       # degrees - góc quét kiếm
SWORD_COOLDOWN = 0.4  # seconds - thời gian hồi giữa các nhát chém

# Robot stats
ROBOT_CONFIGS = {
    'blue': {'color': (50, 120, 255), 'hp': 40, 'speed': 1.5, 'radius': 12, 'dmg': 8, 'fear_light': True},
    'white': {'color': (230, 230, 230), 'hp': 70, 'speed': 1.2, 'radius': 14, 'dmg': 12, 'fear_light': False},
    'green': {'color': (50, 220, 80), 'hp': 80, 'speed': 1.8, 'radius': 12, 'dmg': 10, 'fear_light': False},
    'boss': {'color': (255, 255, 255), 'hp': 300, 'speed': 1.0, 'radius': 28, 'dmg': 25, 'fear_light': False},
    'yellow': {'color': (255, 220, 50), 'hp': 130, 'speed': 1.6, 'radius': 13, 'dmg': 20, 'fear_light': False},
    'white_giant': {'color': (240, 240, 240), 'hp': 300, 'speed': 1.0, 'radius': 28, 'dmg': 25, 'fear_light': False},
}

# Level configs: List of dicts specifying robot counts
LEVEL_ROBOTS = [
    {'blue': 3},                                         # Màn 1: 3 blue
    {'blue': 5, 'green': 3},                             # Màn 2: 5 blue, 3 green
    {'blue': 4, 'yellow': 4, 'green': 3},               # Màn 3: 4 blue, 4 vàng, 3 green
    {'blue': 5, 'green': 5, 'yellow': 5},               # Màn 4: 5 blue, 5 green, 5 vàng
    {'blue': 7, 'green': 7, 'yellow': 5},               # Màn 5: 7 blue, 7 green, 5 vàng
    {'blue': 6, 'yellow': 6, 'green': 6, 'white_giant': 1}, # Màn 6: vàng thay trắng, giữ khổng lồ
]

LEVEL_NAMES = [
    "Thành phố hoang tàn",
    "Khu rừng rậm rạp",
    "Sa mạc chết chóc",
    "Nghĩa địa ma quái",
    "Hầm băng giá",
    "Pháo Đài Tận Thế",
]

LEVEL_BG_COLORS = [
    (45, 45, 55),    # xám tối
    (15, 35, 20),    # xanh đen
    (160, 140, 90),  # cát vàng
    (50, 50, 55),    # xám xịt
    (180, 210, 230), # trắng xanh
    (20, 20, 25),    # nền thép tối (Pháo Đài Tận Thế)
]

LEVEL_WALL_COLORS = [
    (80, 80, 90),
    (30, 70, 30),
    (140, 120, 70),
    (70, 70, 75),
    (150, 180, 200),
    (45, 45, 50),    # tường kim loại
]

# Items
ITEM_TYPES = {
    'battery': {'color': (0, 200, 0), 'symbol': '🔋', 'text': 'PIN', 'effect': 'energy', 'value': 32},
    'medkit': {'color': (255, 80, 80), 'symbol': '🩹', 'text': 'MÁU', 'effect': 'hp', 'value': 22},
    'bulb': {'color': (255, 255, 100), 'symbol': '💡', 'text': 'ĐÈN', 'effect': 'energy', 'value': 20},
    'shoes': {'color': (100, 200, 255), 'symbol': '👟', 'text': 'GIÀY', 'effect': 'speed', 'value': 5},
    'magnet': {'color': (200, 50, 50), 'symbol': '🧲', 'text': 'NC', 'effect': 'magnet', 'value': 3},
    'wave': {'color': (50, 150, 255), 'symbol': '🌊', 'text': 'SÓNG', 'effect': 'wave', 'value': 1},
    'ammo': {'color': (255, 150, 50), 'symbol': '📦', 'text': 'ĐẠN', 'effect': 'ammo', 'value': 12},
}

# Súng và Cấu hình Cửa hàng vũ khí (Trùng khớp 100% hình ảnh)
GUNS_DATA = {
    'pistol': {
        'name': 'Súng Lục',
        'type': 'Pistol',
        'damage': 28,
        'fire_rate': 0.75,
        'clip_size': 15,
        'reload_time': 1.2,
        'price': 0,
        'color': (240, 230, 140),
        'desc': 'Súng lục cơ bản của game. Sát thương ổn định, cực kỳ chính xác.'
    },
    'shotgun': {
        'name': 'Shotgun',
        'type': 'Shotgun',
        'damage': 10,
        'fire_rate': 0.83,
        'clip_size': 6,
        'reload_time': 1.6,
        'price': 500,
        'color': (205, 133, 63),
        'desc': 'Súng bắn đạn chùm tầm gần. Bắn ra 4 tia sát thương quạt rộng.'
    },
    'smg': {
        'name': 'Súng Tiểu Liên',
        'type': 'SMG',
        'damage': 15,
        'fire_rate': 0.08,
        'clip_size': 30,
        'reload_time': 1.1,
        'price': 1000,
        'color': (180, 180, 220),
        'desc': 'Súng liên thanh tầm trung. Tốc độ bắn cực nhanh, xả đạn liên tục.'
    },
    'sniper': {
        'name': 'Súng Tỉa',
        'type': 'Sniper',
        'damage': 150,
        'fire_rate': 1.3,
        'clip_size': 5,
        'reload_time': 1.8,
        'price': 1800,
        'color': (100, 149, 237),
        'desc': 'Súng bắn tỉa hạng nặng. Sát thương cực lớn ở cự ly xa, uy lực khủng khiếp.'
    },
    'advanced_sniper': {
        'name': 'Súng Tỉa Nâng Cấp',
        'type': 'Advanced Sniper',
        'damage': 260,
        'fire_rate': 1.0,
        'clip_size': 8,
        'reload_time': 1.5,
        'price': 2600,
        'color': (255, 127, 80),
        'desc': 'Súng bắn tỉa công nghệ cao. Ống ngắm tiên tiến, nạp đạn nhanh hơn.'
    }
}

# Cấu hình các loại Pet đồng hành (Mục Mua Pet)
PETS_DATA = {
    'mini_robot': {
        'name': 'Mini Robot',
        'desc': 'Tự động sạc pin (+5 năng lượng) mỗi 5 giây.',
        'price': 300,
        'color': (0, 255, 255),
        'effect': 'regen_energy'
    },
    'plasma_pup': {
        'name': 'Plasma Pup',
        'desc': 'Sủa sóng âm đẩy lùi robot ở gần mỗi 4 giây.',
        'price': 500,
        'color': (255, 100, 255),
        'effect': 'sonic_push'
    },
    'lucky_cat': {
        'name': 'Lucky Cat',
        'desc': 'Tăng 50% tỉ lệ rơi vật phẩm xịn từ robot.',
        'price': 800,
        'color': (255, 215, 0),
        'effect': 'better_drops'
    }
}

