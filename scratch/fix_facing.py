import re

with open('entities.py', 'r', encoding='utf-8') as f:
    code = f.read()

old_facing = """        # Cập nhật facing dựa trên delta di chuyển thực tế cho TẤT CẢ robot
        if actually_moved:
            self.is_moving = True
            if abs(dx_moved) > abs(dy_moved):
                self.facing = 'right' if dx_moved > 0 else 'left'
            else:
                self.facing = 'down' if dy_moved > 0 else 'up'
        else:
            self.is_moving = False
            # Khi robot xanh lá hoặc vàng đứng yên nhưng đang nhắm/bắn → cập nhật facing theo góc bắn
            if self.rtype in ['green', 'yellow', 'white_giant'] and dist < 600:
                aim_deg = math.degrees(angle_to_player) % 360
                if 45 <= aim_deg < 135:
                    self.facing = 'down'
                elif 135 <= aim_deg < 225:
                    self.facing = 'left'
                elif 225 <= aim_deg < 315:
                    self.facing = 'up'
                else:
                    self.facing = 'right'"""

new_facing = """        # Cập nhật facing và is_moving
        if actually_moved:
            self.is_moving = True
        else:
            self.is_moving = False
            
        # Luôn luôn hướng mặt về phía người chơi khi ở trong tầm bắn (đối với robot có súng), dù đang di chuyển hay đứng yên
        if self.rtype in ['green', 'yellow', 'white_giant'] and dist < 600:
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
                self.facing = 'down' if dy_moved > 0 else 'up'"""

code = code.replace(old_facing, new_facing)

# Thử trường hợp code cũ (dist < 500) nếu dist < 600 không khớp
old_facing_500 = old_facing.replace("dist < 600:", "dist < 500:")
code = code.replace(old_facing_500, new_facing)

with open('entities.py', 'w', encoding='utf-8') as f:
    f.write(code)
print("Updated facing logic in entities.py")
