"""Pathfinding algorithms: BFS, DFS, A* for grid-based game navigation."""
import math
import heapq
from collections import deque

CELL = 40  # Grid cell size (matches TILE constant)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def world_to_cell(x, y):
    return int(x // CELL), int(y // CELL)

def cell_to_world(cx, cy):
    """Return centre of cell in world coordinates."""
    return cx * CELL + CELL // 2, cy * CELL + CELL // 2

def build_grid(walls, map_w, map_h):
    """Build a 2D boolean grid (True = blocked) from wall rects."""
    cols = math.ceil(map_w / CELL) + 1
    rows = math.ceil(map_h / CELL) + 1
    blocked = [[False] * cols for _ in range(rows)]
    for wall in walls:
        c0 = max(0, int(wall.left  // CELL))
        c1 = min(cols - 1, int(wall.right  // CELL))
        r0 = max(0, int(wall.top   // CELL))
        r1 = min(rows - 1, int(wall.bottom // CELL))
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                blocked[r][c] = True
    return blocked, rows, cols

def get_neighbors(cx, cy, blocked, rows, cols):
    """8-directional neighbours (diagonals allowed)."""
    for dx, dy in [(0,1),(0,-1),(1,0),(-1,0),(1,1),(1,-1),(-1,1),(-1,-1)]:
        nx, ny = cx + dx, cy + dy
        if 0 <= nx < cols and 0 <= ny < rows and not blocked[ny][nx]:
            # Block diagonal if both axis-aligned are blocked (corner cut)
            if dx != 0 and dy != 0:
                if blocked[cy][cx+dx] or blocked[cy+dy][cx]:
                    continue
            yield nx, ny

# ---------------------------------------------------------------------------
# BFS  –  shortest path (unweighted)
# ---------------------------------------------------------------------------

def bfs(start_world, goal_world, walls, map_w, map_h):
    """Return list of world-coord waypoints from start to goal via BFS."""
    blocked, rows, cols = build_grid(walls, map_w, map_h)
    start = world_to_cell(*start_world)
    goal  = world_to_cell(*goal_world)
    if start == goal:
        return []

    parent = {start: None}
    queue  = deque([start])
    found  = False

    while queue:
        cx, cy = queue.popleft()
        if (cx, cy) == goal:
            found = True
            break
        for nx, ny in get_neighbors(cx, cy, blocked, rows, cols):
            if (nx, ny) not in parent:
                parent[(nx, ny)] = (cx, cy)
                queue.append((nx, ny))

    if not found:
        return []

    # Reconstruct path
    path = []
    node = goal
    while node is not None:
        path.append(node)
        node = parent[node]
    path.reverse()
    return [cell_to_world(c, r) for c, r in path[1:]]  # Skip start cell

# ---------------------------------------------------------------------------
# DFS  –  depth-limited depth-first search
# ---------------------------------------------------------------------------

def dfs(start_world, goal_world, walls, map_w, map_h, max_depth=80):
    """Return list of world-coord waypoints from start to goal via DFS."""
    blocked, rows, cols = build_grid(walls, map_w, map_h)
    start = world_to_cell(*start_world)
    goal  = world_to_cell(*goal_world)
    if start == goal:
        return []

    # Iterative DFS with path tracking
    stack   = [(start, [start])]
    visited = set()

    while stack:
        (cx, cy), path = stack.pop()
        if (cx, cy) in visited:
            continue
        visited.add((cx, cy))
        if len(path) > max_depth:
            continue
        for nx, ny in get_neighbors(cx, cy, blocked, rows, cols):
            if (nx, ny) == goal:
                full = path + [(nx, ny)]
                return [cell_to_world(c, r) for c, r in full[1:]]
            if (nx, ny) not in visited:
                stack.append(((nx, ny), path + [(nx, ny)]))
    return []

# ---------------------------------------------------------------------------
# A*  –  optimal weighted path with heuristic
# ---------------------------------------------------------------------------

def astar(start_world, goal_world, walls, map_w, map_h):
    """Return list of world-coord waypoints from start to goal via A*."""
    blocked, rows, cols = build_grid(walls, map_w, map_h)
    start = world_to_cell(*start_world)
    goal  = world_to_cell(*goal_world)
    if start == goal:
        return []

    def h(a, b):
        return math.hypot(a[0]-b[0], a[1]-b[1])

    g_score  = {start: 0.0}
    parent   = {start: None}
    open_set = [(h(start, goal), 0, start)]  # (f, tie_break, node)
    counter  = 1

    while open_set:
        f, _, (cx, cy) = heapq.heappop(open_set)
        if (cx, cy) == goal:
            path = []
            node = goal
            while node is not None:
                path.append(node)
                node = parent[node]
            path.reverse()
            return [cell_to_world(c, r) for c, r in path[1:]]

        for nx, ny in get_neighbors(cx, cy, blocked, rows, cols):
            step = math.hypot(nx-cx, ny-cy)
            tg   = g_score[(cx, cy)] + step
            if tg < g_score.get((nx, ny), float('inf')):
                g_score[(nx, ny)] = tg
                parent[(nx, ny)]  = (cx, cy)
                heapq.heappush(open_set, (tg + h((nx,ny), goal), counter, (nx, ny)))
                counter += 1
    return []
