import pygame
import os
from math import sqrt, sin, cos, radians, floor
import asyncio
import logging
import random
from noise import pnoise2

from scripts.database import init_db, get_db, save_tiles
from scripts.load import load
from scripts.log import log_setup

from world.map import Tile, Terrain
from world.world import tile_list

log_setup("logs/map.log", console=True)
logger = logging.getLogger(__name__)

pygame.init()
os.environ['SDL_VIDEO_WINDOW_POS'] = "50,80"

COAST_BRIGHTENING = 80
def coast_color(color: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
    return (min(255, color[0] + COAST_BRIGHTENING),
            min(255, color[1] + COAST_BRIGHTENING), 
            min(255, color[2] + COAST_BRIGHTENING), 
            BIOME_OPACITY)

BIOME_OPACITY = 150 # 255 = opaque, 0 = transparent
ORE_OPACITY = 255
colors = {
    "water": (0, 70, 150, BIOME_OPACITY),            # slightly darker than the map
    # Tropical
    "rainforest": (0, 92, 42, BIOME_OPACITY),          # deep, saturated green
    "monsoon": (40, 140, 90, BIOME_OPACITY),           # lush but slightly lighter
    "savanna": (230, 200, 80, BIOME_OPACITY),          # yellow-green grassland

    # Hot arid / semi-arid
    "hot_steppe": (210, 200, 120, BIOME_OPACITY),      # pale dry grass
    "hot_desert": (240, 220, 130, BIOME_OPACITY),      # sand yellow

    # Mountains
    "mountains": (90, 90, 90, BIOME_OPACITY),          # dark stone
    "high_mountains": (245, 245, 245, BIOME_OPACITY), # snow / ice

    # Temperate
    "oceanic": (70, 160, 110, BIOME_OPACITY),          # cool maritime green
    "humid_subtropical": (60, 170, 90, BIOME_OPACITY), # warm, wet forests
    "mediterranean": (120, 170, 90, BIOME_OPACITY),    # olive / scrubland

    # Continental / cold
    "humid_continental": (80, 140, 100, BIOME_OPACITY),# mixed forest
    "subarctic_continental": (60, 110, 90, BIOME_OPACITY),
    "cold_steppe": (180, 190, 150, BIOME_OPACITY),     # dry cold grassland
    "cold_desert": (210, 215, 200, BIOME_OPACITY),     # pale, dusty gray

    # Polar
    "tundra": (170, 185, 175, BIOME_OPACITY),          # moss / permafrost
    "ice_caps": (220, 235, 225, BIOME_OPACITY),

    # Land/Water layer
    True: (255, 255, 255, BIOME_OPACITY),
    False: (0, 0, 0, BIOME_OPACITY),

    # Blank terrain values
    None: (0, 0, 0, BIOME_OPACITY)
}

ORE_TYPES = ["iron", "coal", "copper", "gold", "oil"]

SEEDS = {
    "geology": random.randint(1, 100000),
    "iron": random.randint(1, 100000),
    "coal": random.randint(1, 100000),
    "copper": random.randint(1, 100000),
    "gold": random.randint(1, 100000),
    "oil": random.randint(1, 100000),
}

def _hash2(x, y, seed):
    # deterministic integer hash → [0, 1]
    n = x * 374761393 + y * 668265263 + seed * 1442695040888963407
    n = (n ^ (n >> 13)) * 1274126177
    n ^= (n >> 16)
    return (n & 0xFFFFFFFF) / 0xFFFFFFFF


def _smooth(t):
    return t * t * (3 - 2 * t)


def _lerp(a, b, t):
    return a + (b - a) * t


def _value_noise(x, y, seed):
    xi = floor(x)
    yi = floor(y)

    xf = x - xi
    yf = y - yi

    v00 = _hash2(xi, yi, seed)
    v10 = _hash2(xi + 1, yi, seed)
    v01 = _hash2(xi, yi + 1, seed)
    v11 = _hash2(xi + 1, yi + 1, seed)

    u = _smooth(xf)
    v = _smooth(yf)

    x1 = _lerp(v00, v10, u)
    x2 = _lerp(v01, v11, u)

    return _lerp(x1, x2, v)


def sample_noise(x, y, scale, seed):
    # parameters matching your pnoise2 setup
    octaves = 4
    persistence = 0.5
    lacunarity = 2.0

    x *= scale
    y *= scale

    total = 0.0
    amplitude = 1.0
    frequency = 1.0
    norm = 0.0

    for i in range(octaves):
        nx = x * frequency
        ny = y * frequency

        total += _value_noise(nx, ny, seed + i * 1013) * amplitude
        norm += amplitude

        amplitude *= persistence
        frequency *= lacunarity

    n = total / norm  # normalized to ~[0,1]

    # match your original post-processing
    n = n * 0.5 + 0.5

    # safe clamp (NaN-proof)
    if n < 0.0:
        return 0.0
    if n > 1.0:
        return 1.0
    return n

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
    s = total_scale()

    sx = (wx - camera_x + OFFSET_X) * s
    sy = (wy - camera_y + OFFSET_Y) * s

    sx += viewport_w * 0.5 + viewport_offset_x
    sy += viewport_h * 0.5 + viewport_offset_y

    return sx, sy

def world_to_screen_bg(wx, wy):
    s = total_scale()

    sx = (wx - camera_x) * s
    sy = (wy - camera_y) * s

    sx += viewport_w * 0.5 + viewport_offset_x
    sy += viewport_h * 0.5 + viewport_offset_y

    return sx, sy

def total_scale():
    return camera_zoom * viewport_scale

# Convert screen coordinates (sx, sy) -> world coordinates (wx, wy)
def screen_to_world(sx, sy):
    s = total_scale()

    sx -= viewport_w * 0.5 + viewport_offset_x
    sy -= viewport_h * 0.5 + viewport_offset_y

    wx = sx / s + camera_x - OFFSET_X
    wy = sy / s + camera_y - OFFSET_Y

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

# Function to get distance from point to segment
def point_to_segment_distance(px, py, x1, y1, x2, y2):
    # vector from x1,y1 to px,py
    dx, dy = px - x1, py - y1
    # segment vector
    sx, sy = x2 - x1, y2 - y1
    # projection t onto segment
    seg_len_sq = sx*sx + sy*sy
    t = max(0, min(1, (dx*sx + dy*sy) / seg_len_sq)) if seg_len_sq != 0 else 0
    proj_x, proj_y = x1 + t * sx, y1 + t * sy
    return ((px - proj_x)**2 + (py - proj_y)**2)**0.5

FONT = pygame.font.SysFont("consolas", 22)
UI_COLOR = (255, 255, 255)     # white text
UI_BG = (0, 0, 0, 140)         # semi-transparent background
def draw_ui(surface):
    brush_name = current_brush if current_brush is not None else "erase"
    text1 = FONT.render(f"Brush: {brush_name}", True, UI_COLOR)
    text2 = FONT.render(f"Radius: {brush_radius + 1}", True, UI_COLOR)

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

cooldowns = {}
UPDATE_COOLDOWN = 2

async def update_tile(location: tuple[int, int]):
    tile = tile_list.get(location)
    if current_brush == "strait":
        return
    
    if tile is not None:
        if current_brush == None:
            tile_list.pop(location)
            await get_db().execute("DELETE FROM tiles WHERE (x, y) = (?, ?)", location)
            return
        
        if current_brush == "is_water":
            if tile in cooldowns.keys():
                logger.info(f"{location} is on terrain cooldown: {cooldowns[tile]} frames left")
                return

            if tile.terrain.is_water:
                tile.terrain.is_water = False
            else:
                tile.terrain.is_water = True
            cooldowns[tile] = UPDATE_COOLDOWN

        elif current_brush == "is_land":
            if tile in cooldowns.keys():
                logger.info(f"{location} is on terrain cooldown: {cooldowns[tile]} frames left")
                return
            
            if tile.terrain.is_land:
                tile.terrain.is_land = False
            else:
                tile.terrain.is_land = True
            cooldowns[tile] = UPDATE_COOLDOWN

        else:
            tile.terrain.biome = current_brush
        await tile.save()
        return
    
    if current_brush == "is_land" or current_brush == None:
        return
    
    if current_brush == "is_water":
        terrain = Terrain(
            biome="water",
            is_land=False,
            is_water=True,
            difficulty=0
        )
    else:
        terrain = Terrain(
            biome=current_brush,
            is_land=True,
            is_water=False,
            difficulty=0
        )
    new_tile = Tile(
        terrain=terrain,
        location=location
    )
    tile_list.update({
        location: new_tile
    })
    await new_tile.save()

# ===== MAIN LOOP =====

async def main():
    # ===== SETTINGS =====
    ADJUST_STEP = 0.02
    ZOOM_STEP = 1.1
    MIN_ZOOM = 1.0
    MAX_ZOOM = 5.0

    global OFFSET_X, OFFSET_Y, HEX_SIZE
    HEX_SIZE = 7.876
    OFFSET_X = 5.54  # Offsets are for hex grid alignment
    OFFSET_Y = 8.30 

    RAW_MAP = pygame.image.load("assets\\map.png")

    global SCREEN_W, SCREEN_H
    BG_NATIVE_W, BG_NATIVE_H = (n / 5 for n in RAW_MAP.get_size())

    # Background world rectangle
    bg_world_left   = -BG_NATIVE_W / 2
    bg_world_top    = -BG_NATIVE_H / 2
    bg_world_right  =  BG_NATIVE_W / 2
    bg_world_bottom =  BG_NATIVE_H / 2

    SCREEN_W, SCREEN_H = BG_NATIVE_W, BG_NATIVE_H

    SCREEN = pygame.display.set_mode((SCREEN_W, SCREEN_H), pygame.RESIZABLE)

    terrain_file = "data\\map.db"

    global current_brush
    current_brush = "rainforest"
    mouse_down = False
    panning = False
    layer = "biome"

    global brush_radius
    brush_radius = 0
    global camera_zoom
    camera_zoom = 1.0
    global camera_x
    camera_x = 0.0
    global camera_y
    camera_y = 0.0
    global viewport_scale, viewport_offset_x, viewport_offset_y, viewport_w, viewport_h
    viewport_scale = 1.0
    viewport_offset_x = 0.0
    viewport_offset_y = 0.0
    viewport_w = BG_NATIVE_W
    viewport_h = BG_NATIVE_H

    await init_db(file=terrain_file)
    await load(map_only=True)

    # logger.info("Generating ore richness...")

    # count = 0
    # for (q, r), tile in list(tile_list.items()):
    #     count += 1
    #     # Skip ocean
    #     if not tile.terrain.is_land:
    #         continue
        
    #     wx = (3/2) * q
    #     wy = (sqrt(3)/2 * q + sqrt(3) * r)

    #     # Broad geological provinces
    #     geology = sample_noise(wx, wy, 0.03, SEEDS["geology"])

    #     # Terrain modifiers
    #     mountain_factor = 1.0

    #     if tile.terrain.biome == "mountains":
    #         mountain_factor = 1.1

    #     elif tile.terrain.biome == "high_mountains":
    #         mountain_factor = 1.8

    #     ores = {}

    #     # ===== IRON =====
    #     iron = sample_noise(wx, wy, 0.08, SEEDS["iron"])
    #     iron *= geology
    #     iron *= mountain_factor
    #     iron = max(0.0, min(1.0, iron)) ** 6

    #     # ===== COAL =====
    #     coal = sample_noise(wx, wy, 0.14, SEEDS["coal"])
    #     coal *= geology
    #     coal *= mountain_factor * 1.4
    #     coal = max(0.0, min(1.0, coal)) ** 6

    #     # ===== COPPER =====
    #     copper = sample_noise(wx, wy, 0.10, SEEDS["copper"])
    #     copper *= geology * 1.2
    #     copper *= mountain_factor
    #     copper = max(0.0, min(1.0, copper)) ** 6

    #     # ===== GOLD =====
    #     gold = sample_noise(wx, wy, 0.06, SEEDS["gold"])
    #     gold *= (1.2 - abs(geology - 0.5))
    #     gold *= max(1.0, mountain_factor * 0.8)
    #     gold = max(0.0, min(1.0, gold)) ** 6

    #     # ===== OIL =====
    #     oil = sample_noise(wx, wy, 0.25, SEEDS["oil"])

    #     # Oil prefers flat dry regions
    #     if tile.terrain.biome in [
    #         "hot_desert",
    #         "cold_desert",
    #         "hot_steppe",
    #         "cold_steppe"
    #     ]:
    #         oil *= 1.2

    #     if mountain_factor > 1.0:
    #         oil *= 0.3

    #     oil = max(0.0, min(1.0, oil)) ** 7

    #     ores["iron"] = min(1.0, iron)
    #     ores["coal"] = min(1.0, coal)
    #     ores["copper"] = min(1.0, copper)
    #     ores["gold"] = min(1.0, gold)
    #     ores["oil"] = min(1.0, oil)

    #     tile.terrain.ores = ores

    # logger.info("Finished ore generation.")

    # await save_tiles(tile_list.values())

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
                q, r = pixel_to_hex(mx, my)
                    
                # Left click = paint with current brush
                if event.button == 1 and not pygame.key.get_pressed()[pygame.K_SPACE]:
                    if current_brush == "strait":
                        # Compute center of hex in screen coords
                        hx, hy = hex_to_pixel(q, r)

                        # Compute world-space corners scaled by HEX_SIZE
                        corners = [(hx + HEX_SIZE * ux, hy + HEX_SIZE * uy) for (ux, uy) in UNIT_HEX]

                        # Compute distance to each hex side
                        side_distances = [point_to_segment_distance(mx, my,
                                                                    corners[i][0], corners[i][1],
                                                                    corners[(i+1)%6][0], corners[(i+1)%6][1])
                                        for i in range(6)]
                        
                        # Closest side index
                        closest_side = side_distances.index(min(side_distances))
                        # indexed as 0: NE, 1: N, 2: NW ...

                        # Apply strait logic for that side here
                        tile = tile_list.get((q, r))
                        if tile is None:
                            pass
                        elif closest_side not in tile.terrain.straits:
                            tile.terrain.straits.append(closest_side)
                            await tile.save()
                        elif closest_side in tile.terrain.straits:
                            tile.terrain.straits.remove(closest_side)
                            await tile.save()
                    
                    else:
                        for qq, rr in hex_range(q, r, brush_radius):
                            await update_tile((qq, rr))
                            logger.info(f"Wrote to hex {qq, rr}")
                
                # Left click + space = start panning
                if event.button == 1 and pygame.key.get_pressed()[pygame.K_SPACE]:
                    panning = True
                    pan_start = pygame.mouse.get_pos()
                    camera_start = (camera_x, camera_y)
                
            if event.type == pygame.MOUSEBUTTONUP:
                if event.button in (1, 3):
                    mouse_down = False
                if event.button == 1 and panning:
                    panning = False

            # ==========================
            #   KEY INPUT
            # ==========================
            if event.type == pygame.KEYDOWN:

                # Save
                if event.key == pygame.K_ESCAPE:
                    await get_db().commit()
                    logger.info(f"Overlay alignment values are currently: (SIZE: {HEX_SIZE}), (X: {OFFSET_X}), (Y: {OFFSET_Y}) ")

                # ==== Layer selection ====
                elif event.key == pygame.K_F1:
                    layer = "biome"
                elif event.key == pygame.K_F2:
                    layer = "iron"
                elif event.key == pygame.K_F3:
                    layer = "copper"
                elif event.key == pygame.K_F4:
                    layer = "gold"
                elif event.key == pygame.K_F5:
                    layer = "coal"
                elif event.key == pygame.K_F6:
                    layer = "oil"

                # ==== Brush selection ====
                elif event.key == pygame.K_1:
                    current_brush = "rainforest"

                elif event.key == pygame.K_2:
                    current_brush = "monsoon"

                elif event.key == pygame.K_3:
                    current_brush = "savanna"

                elif event.key == pygame.K_4:
                    current_brush = "hot_steppe"

                elif event.key == pygame.K_5:
                    current_brush = "hot_desert"

                elif event.key == pygame.K_6:
                    current_brush = "mountains"

                elif event.key == pygame.K_7:
                    current_brush = "high_mountains"
                
                elif event.key == pygame.K_8:
                    current_brush = "subarctic_continental"

                elif event.key == pygame.K_q:
                    current_brush = "oceanic"
                
                elif event.key == pygame.K_w:
                    current_brush = "humid_subtropical"

                elif event.key == pygame.K_e:
                    current_brush = "humid_continental"
                
                elif event.key == pygame.K_r:
                    current_brush = "cold_steppe"

                elif event.key == pygame.K_t:
                    current_brush = "cold_desert"
                
                elif event.key == pygame.K_y:
                    current_brush = "mediterranean"
                
                elif event.key == pygame.K_u:
                    current_brush = "tundra"
                
                elif event.key == pygame.K_i:
                    current_brush = "ice_caps"
                
                elif event.key == pygame.K_a:
                    current_brush = "is_land"

                elif event.key == pygame.K_s:
                    current_brush = "is_water"
                
                elif event.key == pygame.K_d:
                    current_brush = "strait"

                elif event.key == pygame.K_z:
                    current_brush = None
                
                # ==== Brush size ====
                elif event.key == pygame.K_LEFTBRACKET:
                    brush_radius = max(0, brush_radius - 1)

                elif event.key == pygame.K_RIGHTBRACKET:
                    brush_radius = min(5, brush_radius + 1)

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
                    camera_zoom = min(MAX_ZOOM, camera_zoom * ZOOM_STEP)
                else:
                    camera_zoom = max(MIN_ZOOM, camera_zoom / ZOOM_STEP)

            if event.type == pygame.VIDEORESIZE:
                SCREEN_W, SCREEN_H = event.w, event.h
                SCREEN = pygame.display.set_mode((SCREEN_W, SCREEN_H), pygame.RESIZABLE)

        # ==========================
        #   DRAG PAINTING
        # ==========================
        if mouse_down and not pygame.key.get_pressed()[pygame.K_SPACE]:
            mx, my = pygame.mouse.get_pos()
            q, r = pixel_to_hex(mx, my)

            # Left drag = paint
            if pygame.mouse.get_pressed()[0]:
                for qq, rr in hex_range(q, r, brush_radius):
                    await update_tile((qq, rr))

        # ==== Pan ====
        if panning:
            mx, my = pygame.mouse.get_pos()
            dx = (mx - pan_start[0]) / camera_zoom
            dy = (my - pan_start[1]) / camera_zoom
            camera_x = camera_start[0] - dx
            camera_y = camera_start[1] - dy

        # ==========================
        #   DRAW
        # ==========================
        # Fills black to make a blank background
        SCREEN.fill((0, 0, 0))

        # calculate ideal scaling factor, allowing for letterboxing
        scale_x = SCREEN_W / BG_NATIVE_W
        scale_y = SCREEN_H / BG_NATIVE_H
        viewport_scale = min(scale_x, scale_y)

        viewport_w = int(BG_NATIVE_W * viewport_scale)
        viewport_h = int(BG_NATIVE_H * viewport_scale)

        # where that world top-left maps on screen
        viewport_offset_x = (SCREEN_W - viewport_w) // 2
        viewport_offset_y = (SCREEN_H - viewport_h) // 2

        tl = world_to_screen_bg(bg_world_left, bg_world_top)
        br = world_to_screen_bg(bg_world_right, bg_world_bottom)

        bg_screen_w = int(br[0] - tl[0])
        bg_screen_h = int(br[1] - tl[1])

        if bg_screen_w > 0 and bg_screen_h > 0:
            bg_scaled = pygame.transform.smoothscale(RAW_MAP, (bg_screen_w, bg_screen_h))

            # blit scaled background at that screen position
            SCREEN.blit(bg_scaled, tl)

        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        for (q, r), tile in tile_list.items():
            # compute center in world-space
            wx, wy = hex_to_pixel(q, r, world=True)
            # build world-space corners using actual HEX_SIZE
            world_corners = [(wx + HEX_SIZE * ux, wy + HEX_SIZE * uy) for (ux, uy) in UNIT_HEX]
            # convert corners to screen-space using the exact same transform used for the background
            screen_corners = [world_to_screen(cx, cy) for (cx, cy) in world_corners]
            
            if layer == "biome":
                info = tile.terrain.biome
                # draw base hex
                color = colors[info]
                if tile.terrain.is_land and tile.terrain.is_water:
                    color = coast_color(color)
                pygame.draw.polygon(overlay, color, screen_corners, 0)
                pygame.draw.polygon(overlay, (0, 0, 0, 255), screen_corners, 1)

                # draw straits
                if getattr(tile.terrain, "straits", None):
                    for side in tile.terrain.straits:
                        start_idx = side
                        end_idx = (side + 1) % 6
                        pygame.draw.line(
                            overlay,
                            (0,0,0,255),
                            screen_corners[start_idx],
                            screen_corners[end_idx],
                            int(5 * viewport_scale)  # thickness of the strait line
                        )
                
                # update terrain update cooldowns
                if tile in cooldowns:
                    cooldowns[tile] -= 1
                    if cooldowns[tile] <= 0:
                        cooldowns.pop(tile)
            
            elif layer in ORE_TYPES:
                info = tile.terrain.ores.get(layer, 0.0)

                # Clamp safely
                value = max(0.0, min(1.0, info))

                # ===== HEATMAP COLORING =====
                # Most tiles dark, rich deposits glow brightly

                if value <= 0.001:
                    # Almost none
                    color = (15, 15, 15, ORE_OPACITY)

                else:
                    # Strong nonlinear brightness
                    brightness = value ** 0.4

                    match layer:
                        case "iron":
                            color = (
                                int(140 * brightness + 40),
                                int(80 * brightness + 30),
                                int(60 * brightness + 20),
                                ORE_OPACITY
                            )

                        case "coal":
                            color = (
                                int(50 * brightness + 10),
                                int(50 * brightness + 10),
                                int(50 * brightness + 10),
                                ORE_OPACITY
                            )

                        case "copper":
                            color = (
                                int(180 * brightness + 40),
                                int(110 * brightness + 30),
                                int(60 * brightness + 20),
                                ORE_OPACITY
                            )

                        case "gold":
                            color = (
                                int(255 * brightness),
                                int(215 * brightness),
                                int(60 * brightness + 20),
                                ORE_OPACITY
                            )

                        case "oil":
                            color = (
                                int(30 * brightness + 10),
                                int(120 * brightness + 20),
                                int(40 * brightness + 10),
                                ORE_OPACITY
                            )

                        case _:
                            gray = int(255 * brightness)
                            color = (gray, gray, gray, BIOME_OPACITY)

                pygame.draw.polygon(overlay, color, screen_corners, 0)
                pygame.draw.polygon(overlay, (0, 0, 0, 255), screen_corners, 1)

        SCREEN.blit(overlay, (0, 0))
        draw_ui(SCREEN)

        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    asyncio.run(main(), debug=True)