import pygame
import os
from math import sqrt, sin, cos, pi, radians
import asyncio
import logging

from scripts.database import init_db, get_db
from scripts.load import load
from scripts.log import log_setup

from world.map import Tile, Terrain
from world.world import tile_list

log_setup("logs/map.log", console=True)
logger = logging.getLogger(__name__)

pygame.init()
os.environ['SDL_VIDEO_WINDOW_POS'] = "50,80"

# Note: x in [-65, 64] & y in [-73, 72]

COAST_BRIGHTENING = 80
def coast_color(color: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
    return (min(255, color[0] + COAST_BRIGHTENING),
            min(255, color[1] + COAST_BRIGHTENING), 
            min(255, color[2] + COAST_BRIGHTENING), 
            HEX_OPACITY)

HEX_OPACITY = 100 # 255 = opaque, 0 = transparent
colors = {
    "water": (0, 70, 150, HEX_OPACITY),            # slightly darker than the map
    # Tropical
    "rainforest": (0, 92, 42, HEX_OPACITY),          # deep, saturated green
    "monsoon": (40, 140, 90, HEX_OPACITY),           # lush but slightly lighter
    "savanna": (230, 200, 80, HEX_OPACITY),          # yellow-green grassland

    # Hot arid / semi-arid
    "hot_steppe": (210, 200, 120, HEX_OPACITY),      # pale dry grass
    "hot_desert": (240, 220, 130, HEX_OPACITY),      # sand yellow

    # Mountains
    "mountains": (90, 90, 90, HEX_OPACITY),          # dark stone
    "high_mountains": (245, 245, 245, HEX_OPACITY), # snow / ice

    # Temperate
    "oceanic": (70, 160, 110, HEX_OPACITY),          # cool maritime green
    "humid_subtropical": (60, 170, 90, HEX_OPACITY), # warm, wet forests
    "mediterranean": (120, 170, 90, HEX_OPACITY),    # olive / scrubland

    # Continental / cold
    "humid_continental": (80, 140, 100, HEX_OPACITY),# mixed forest
    "subarctic_continental": (60, 110, 90, HEX_OPACITY),
    "cold_steppe": (180, 190, 150, HEX_OPACITY),     # dry cold grassland
    "cold_desert": (210, 215, 200, HEX_OPACITY),     # pale, dusty gray

    # Polar
    "tundra": (170, 185, 175, HEX_OPACITY),          # moss / permafrost
    "ice_caps": (220, 235, 225, HEX_OPACITY),

    # Land/Water layer
    True: (255, 255, 255, HEX_OPACITY),
    False: (0, 0, 0, HEX_OPACITY),

    # Blank terrain values
    None: (0, 0, 0, HEX_OPACITY)
}

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

    RAW_MAP = pygame.image.load("map.png")

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

                # ==== Brush selection ====
                if event.key == pygame.K_1:
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
            match layer:
                case "biome":
                    info = tile.terrain.biome
                case "is_land":
                    info = tile.terrain.is_land
            if not info:
                continue

            # compute center in world-space
            wx, wy = hex_to_pixel(q, r, world=True)

            # build world-space corners using actual HEX_SIZE
            world_corners = [(wx + HEX_SIZE * ux, wy + HEX_SIZE * uy) for (ux, uy) in UNIT_HEX]

            # convert corners to screen-space using the exact same transform used for the background
            screen_corners = [world_to_screen(cx, cy) for (cx, cy) in world_corners]

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

        SCREEN.blit(overlay, (0, 0))
        draw_ui(SCREEN)

        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    asyncio.run(main())