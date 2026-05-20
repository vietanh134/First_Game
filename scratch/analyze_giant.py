from PIL import Image

img = Image.open('khổng lồ.png')
if img.mode != 'RGBA':
    img = img.convert('RGBA')

w, h = img.size
pixels = img.load()

visited = set()
boxes = []

def bfs(start_x, start_y):
    q = [(start_x, start_y)]
    visited.add((start_x, start_y))
    min_x, max_x = start_x, start_x
    min_y, max_y = start_y, start_y
    
    while q:
        x, y = q.pop(0)
        for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (-1, -1), (1, -1), (-1, 1)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < w and 0 <= ny < h and (nx, ny) not in visited:
                _, _, _, a = pixels[nx, ny]
                if a > 10:  # Not fully transparent
                    visited.add((nx, ny))
                    q.append((nx, ny))
                    min_x = min(min_x, nx)
                    max_x = max(max_x, nx)
                    min_y = min(min_y, ny)
                    max_y = max(max_y, ny)
    return min_x, min_y, max_x, max_y

for y in range(h):
    for x in range(w):
        if (x, y) not in visited:
            _, _, _, a = pixels[x, y]
            if a > 10:
                min_x, min_y, max_x, max_y = bfs(x, y)
                if max_x - min_x > 10 and max_y - min_y > 10:
                    boxes.append((min_x, min_y, max_x - min_x + 1, max_y - min_y + 1))

boxes.sort(key=lambda b: (b[1] // 50, b[0]))
print(f"Found {len(boxes)} sprites")
for i, b in enumerate(boxes):
    print(f"Sprite {i}: {b}")
