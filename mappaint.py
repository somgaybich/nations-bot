import pygame
import json
import os
from math import sqrt, sin, cos, pi, radians

pygame.init()
os.environ['SDL_VIDEO_WINDOW_POS'] = "50,80"

# Note: x in [-65, 64] & y in [-73, 72]

# ===== SETTINGS =====
HEX_SIZE = 9.84
HEX_OPACITY = 100 # 255 = opaque, 0 = transparent
COAST_BRIGHTENING = 80
OFFSET_X = 7.54  # Offsets are for hex grid alignment
OFFSET_Y = 9.4 
ADJUST_STEP = 0.02
BRUSH_RADIUS = 0   

CAMERA_ZOOM = 1.0
CAMERA_X = 0.0
CAMERA_Y = 0.0
ZOOM_STEP = 1.1
MIN_ZOOM = 0.2
MAX_ZOOM = 5.0

FONT = pygame.font.SysFont("consolas", 22)
UI_COLOR = (255, 255, 255)     # white text
UI_BG = (0, 0, 0, 140)         # semi-transparent background

SCREEN_W, SCREEN_H = 1924, 1378
SCREEN = pygame.display.set_mode((SCREEN_W, SCREEN_H))
RAW_MAP = pygame.image.load("worldmap.png")
BACKGROUND = pygame.transform.smoothscale(RAW_MAP, (SCREEN_W, SCREEN_H))

terrain_file = "data\\tiles.json"
terrain = {}

if os.path.exists(terrain_file):
    try:
        with open(terrain_file, "r") as f:
            raw = json.load(f)
        # Convert string keys like "(3, -2)" back into tuples (3, -2)
        for key, value in raw.items():
            q, r = map(int, key.strip("()").split(","))
            terrain[(q, r)] = value
        print("Loaded terrain.json")
    except Exception as e:
        print(f"Error loading terrain.json: {e}")
else:
    print("No terrain.json found; starting with blank terrain.")

current_brush = "ocean"
mouse_down = False
panning = False

def coast_color(color: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
    return (min(255, color[0] + COAST_BRIGHTENING),
            min(255, color[1] + COAST_BRIGHTENING), 
            min(255, color[2] + COAST_BRIGHTENING), 
            HEX_OPACITY)

colors = {
    "ocean": (0, 0, 255, HEX_OPACITY),
    "plains": (100, 255, 0, HEX_OPACITY),
    "forest": (0, 68, 33, HEX_OPACITY),
    "desert": (255, 255, 0, HEX_OPACITY),
    "mountains": (50, 50, 50, HEX_OPACITY),
    "high_mountains": (255, 255, 255, HEX_OPACITY),
}

colors.update({
    "plains_coast": coast_color(colors["plains"]),
    "forest_coast": coast_color(colors["forest"]),
    "desert_coast": coast_color(colors["desert"]),
    "mountains_coast": coast_color(colors["mountains"])
})

# ===== HEX MATH =====

def hex_range(q, r, radius):
    """Return all hexes within 'radius' of (q, r) in axial coords."""
    results = []
    for dq in range(-radius, radius + 1):
        for dr in range(-radius, radius + 1):
            if abs(dq + dr) <= radius:
                results.append((q + dq, r + dr))
    return results

def cube_round(q, r):
    x, z = q, r
    y = -x - z
    rx, ry, rz = round(x), round(y), round(z)
    dx, dy, dz = abs(rx - x), abs(ry - y), abs(rz - z)
    if dx > dy and dx > dz:
        rx = -ry - rz
    elif dy > dz:
        ry = -rx - rz
    else:
        rz = -rx - ry
    return rx, rz

UNIT_HEX = [(cos(radians(60 * i)), sin(radians(60 * i))) for i in range(6)]

# Convert world coordinates (wx, wy) -> screen coordinates (sx, sy)
def world_to_screen(wx, wy):
    sx = (wx + CAMERA_X) * CAMERA_ZOOM + SCREEN_W / 2 + OFFSET_X * CAMERA_ZOOM
    sy = (wy + CAMERA_Y) * CAMERA_ZOOM + SCREEN_H / 2 + OFFSET_Y * CAMERA_ZOOM
    return sx, sy

def world_to_screen_bg(wx, wy):
    sx = (wx + CAMERA_X) * CAMERA_ZOOM + SCREEN_W / 2
    sy = (wy + CAMERA_Y) * CAMERA_ZOOM + SCREEN_H / 2
    return sx, sy

# Convert screen coordinates (sx, sy) -> world coordinates (wx, wy)
def screen_to_world(sx, sy):
    # undo screen center + offset, then undo zoom and camera pan
    px = sx - (SCREEN_W / 2 + OFFSET_X)
    py = sy - (SCREEN_H / 2 + OFFSET_Y)
    wx = px / CAMERA_ZOOM - CAMERA_X
    wy = py / CAMERA_ZOOM - CAMERA_Y
    return wx, wy

# hex_to_pixel now can return world-space coords when world=True
def hex_to_pixel(q, r, world=False):
    # world-space center of the hex
    x = HEX_SIZE * (3/2 * q)
    y = HEX_SIZE * (sqrt(3)/2 * q + sqrt(3) * r)
    if world:
        return x, y
    return world_to_screen(x, y)

# pixel_to_hex should convert screen coords -> world -> hex
def pixel_to_hex(px, py):
    wx, wy = screen_to_world(px, py)
    q = (2/3 * wx) / HEX_SIZE
    r = (-1/3 * wx + sqrt(3)/3 * wy) / HEX_SIZE
    return cube_round(q, r)

def draw_ui(surface):
    brush_name = current_brush if current_brush is not None else "erase"
    text1 = FONT.render(f"Brush: {brush_name}", True, UI_COLOR)
    text2 = FONT.render(f"Radius: {BRUSH_RADIUS + 1}", True, UI_COLOR)

    # Background box (slightly larger than text)
    padding = 6
    w = max(text1.get_width(), text2.get_width()) + padding*2
    h = text1.get_height() + text2.get_height() + padding*3

    ui_box = pygame.Surface((w, h), pygame.SRCALPHA)
    ui_box.fill(UI_BG)

    # Draw text inside
    ui_box.blit(text1, (padding, padding))
    ui_box.blit(text2, (padding, padding + text1.get_height() + 4))

    # Blit UI at top-left of screen
    surface.blit(ui_box, (10, 10))

# ===== MAIN LOOP =====

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # ==========================
        #   MOUSE INPUT
        # ==========================
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_down = True
            mx, my = pygame.mouse.get_pos()
            q, r = pixel_to_hex(mx - OFFSET_X * CAMERA_ZOOM, my - OFFSET_Y * CAMERA_ZOOM)

            # Left click = paint with current brush
            if event.button == 1 and not pygame.key.get_pressed()[pygame.K_SPACE]:
                if current_brush is None:
                    for qq, rr in hex_range(q, r, BRUSH_RADIUS):
                        terrain.pop((qq, rr), None)
                else:
                    for qq, rr in hex_range(q, r, BRUSH_RADIUS):
                        print(f"Wrote to hex {qq, rr}")
                        if (qq, rr) in terrain:
                            terrain[(qq, rr)]["terrain"] = current_brush
                        else:
                            terrain.update({
                                (qq, rr): {"terrain": current_brush}
                            })

            # Right click = always erase
            if event.button == 3:
                terrain.pop((q, r), None)
            
            # Holding space + left click = start panning
            if event.button == 1 and pygame.key.get_pressed()[pygame.K_SPACE]:
                panning = True
                pan_start = pygame.mouse.get_pos()
                camera_start = (CAMERA_X, CAMERA_Y)

        if event.type == pygame.MOUSEBUTTONUP:
            if event.button in (1, 3):
                mouse_down = False
            if event.button == 1 and panning:
                panning = False

        # ==========================
        #   KEY INPUT
        # ==========================
        if event.type == pygame.KEYDOWN:
            mods = event.mod

            # Save
            if event.key == pygame.K_s:
                json.dump({str(k): v for k, v in terrain.items()}, open(terrain_file, "w"), indent=2)
                print(f"Saved {terrain_file}")

            def choose_variant(base_name):
                if mods & pygame.KMOD_SHIFT:
                    coast_name = f"{base_name}_coast"
                    if coast_name in colors:
                        return coast_name
                    else:
                        print(f"No coast variant for '{base_name}'.")
                        return base_name
                return base_name

            # ==== Brush selection ====
            if event.key == pygame.K_1:
                current_brush = "ocean"

            elif event.key == pygame.K_2:
                current_brush = choose_variant("plains")
            elif event.key == pygame.K_3:
                current_brush = choose_variant("forest")

            elif event.key == pygame.K_4:
                current_brush = choose_variant("desert")

            elif event.key == pygame.K_5:
                current_brush = choose_variant("mountains")

            elif event.key == pygame.K_6:
                current_brush = "high_mountains"

            elif event.key == pygame.K_0:
                current_brush = None
            
            # ==== Brush size ====
            elif event.key == pygame.K_LEFTBRACKET:
                BRUSH_RADIUS = max(0, BRUSH_RADIUS - 1)

            elif event.key == pygame.K_RIGHTBRACKET:
                BRUSH_RADIUS = min(5, BRUSH_RADIUS + 1)

            # ==== Alignment ====
            # Size
            elif event.key == pygame.K_EQUALS:  # + key
                HEX_SIZE += ADJUST_STEP
            elif event.key == pygame.K_MINUS:   # - key
                HEX_SIZE = max(1, HEX_SIZE - ADJUST_STEP)

            # OFFSET_X
            elif event.key == pygame.K_RIGHT:
                OFFSET_X += ADJUST_STEP
            elif event.key == pygame.K_LEFT:
                OFFSET_X -= ADJUST_STEP

            # OFFSET_Y
            elif event.key == pygame.K_DOWN:
                OFFSET_Y += ADJUST_STEP
            elif event.key == pygame.K_UP:
                OFFSET_Y -= ADJUST_STEP
            
        # ==== Zoom ====
        if event.type == pygame.MOUSEWHEEL:
            if event.y >0:
                CAMERA_ZOOM = min(MAX_ZOOM, CAMERA_ZOOM * ZOOM_STEP)
            else:
                CAMERA_ZOOM = max(MIN_ZOOM, CAMERA_ZOOM / ZOOM_STEP)

    # ==========================
    #   DRAG PAINTING
    # ==========================
    if mouse_down and not pygame.key.get_pressed()[pygame.K_SPACE]:
        mx, my = pygame.mouse.get_pos()
        q, r = pixel_to_hex(mx - OFFSET_X * CAMERA_ZOOM, my - OFFSET_Y * CAMERA_ZOOM)

        # Left drag = paint
        if pygame.mouse.get_pressed()[0]:
            if current_brush is None:
                for qq, rr in hex_range(q, r, BRUSH_RADIUS):
                    terrain.pop((qq, rr), None)
            else:
                for qq, rr in hex_range(q, r, BRUSH_RADIUS):
                    terrain[(qq, rr)]["terrain"] = current_brush

        # Right drag = erase
        if pygame.mouse.get_pressed()[2]:
            terrain.pop((q, r), None)

    # ==== Pan ====
    if panning:
        mx, my = pygame.mouse.get_pos()
        dx = (mx - pan_start[0]) / CAMERA_ZOOM
        dy = (my - pan_start[1]) / CAMERA_ZOOM
        CAMERA_X = camera_start[0] + dx
        CAMERA_Y = camera_start[1] + dy

    # ==========================
    #   DRAW
    # ==========================
    # background world rectangle spans from (-SCREEN_W/2, -SCREEN_H/2) to (+SCREEN_W/2, +SCREEN_H/2)
    bg_w = int(SCREEN_W * CAMERA_ZOOM)
    bg_h = int(SCREEN_H * CAMERA_ZOOM)
    bg_scaled = pygame.transform.smoothscale(BACKGROUND, (bg_w, bg_h))

    # world top-left of the background
    bg_world_tl_x = -SCREEN_W / 2
    bg_world_tl_y = -SCREEN_H / 2

    # where that world top-left maps on screen
    bg_screen_x, bg_screen_y = world_to_screen_bg(bg_world_tl_x, bg_world_tl_y)

    # blit scaled background at that screen position
    SCREEN.blit(bg_scaled, (int(bg_screen_x), int(bg_screen_y)))

    overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    for (q, r), tile in terrain.items():
        t = tile['terrain']
        if not t:
            continue

        # compute center in world-space
        wx, wy = hex_to_pixel(q, r, world=True)

        # build world-space corners using actual HEX_SIZE
        world_corners = [(wx + HEX_SIZE * ux, wy + HEX_SIZE * uy) for (ux, uy) in UNIT_HEX]

        # convert corners to screen-space using the exact same transform used for the background
        screen_corners = [world_to_screen(cx, cy) for (cx, cy) in world_corners]

        color = colors[t]
        pygame.draw.polygon(overlay, color, screen_corners, 0)
        pygame.draw.polygon(overlay, (0, 0, 0, 255), screen_corners, 1)

    SCREEN.blit(overlay, (0, 0))
    draw_ui(SCREEN)

    pygame.display.flip()

pygame.quit()