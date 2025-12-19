from PIL import Image
import logging
import math
import traceback

from scripts.nations import tiles, TileList, City

logger = logging.getLogger(__name__)

HEX_WIDTH  = 90
HEX_HEIGHT = 80
HEX_SIZE = HEX_WIDTH / 2
X_SPACING = HEX_WIDTH * 3/4
Y_SPACING = HEX_HEIGHT

terrain_sprites = {
    "ocean": Image.open("assets/terrain/ocean.png").convert("RGBA"),
    "plains": Image.open("assets/terrain/plains.png").convert("RGBA"),
    "forest": Image.open("assets/terrain/forest.png").convert("RGBA"),
    "desert": Image.open("assets/terrain/desert.png").convert("RGBA"),
    "mountains": Image.open("assets/terrain/mountains.png").convert("RGBA"),
    "high_mountains": Image.open("assets/terrain/high_mountains.png").convert("RGBA"),
}
overlay_sprites = {
    "rail_n": Image.open("assets/overlays/rail_n.png").convert("RGBA"),
    "rail_ne": Image.open("assets/overlays/rail_ne.png").convert("RGBA"),
    "rail_se": Image.open("assets/overlays/rail_se.png").convert("RGBA"),
    "rail_s": Image.open("assets/overlays/rail_s.png").convert("RGBA"),
    "rail_sw": Image.open("assets/overlays/rail_sw.png").convert("RGBA"),
    "rail_nw": Image.open("assets/overlays/rail_nw.png").convert("RGBA"),
    "outpost": Image.open("assets/overlays/outpost.png").convert("RGBA"),
    "village": Image.open("assets/overlays/village.png").convert("RGBA"),
    "town": Image.open("assets/overlays/town.png").convert("RGBA"),
    "city": Image.open("assets/overlays/city.png").convert("RGBA"),
    "metropolis": Image.open("assets/overlays/metropolis.png").convert("RGBA"),
}
tier_names = {
    0: "outpost",
    1: "village",
    2: "town",
    3: "city",
    4: "metropolis"
}

def render_snapshot(corner1, corner2, padding=0):
    """
    Makes a map image from a specific screen-space rectangle given by two axial corners.
    corner1, corner2 are (q, r) axial coordinates (these are the screen-space rectangle corners).
    Returns a PIL Image.
    """
    try:
        # Recompute u/v rectangle here (flat-top)
        def uv(q, r):
            return q, r + q / 2

        q1, r1 = corner1
        q2, r2 = corner2
        u1, v1 = uv(q1, r1)
        u2, v2 = uv(q2, r2)

        u_min, u_max = min(u1, u2), max(u1, u2)
        v_min, v_max = min(v1, v2), max(v1, v2)

        # conservative q range (integers)
        q_min = math.ceil(u_min)
        q_max = math.floor(u_max)

        # collect tiles whose (u,v) lies inside the rectangle
        selected = TileList()
        for key, tile in tiles.items():
            # defend against bad keys
            try:
                q, r = key
            except Exception:
                continue

            u = q
            v = r + q / 2.0
            if u_min <= u <= u_max and v_min <= v <= v_max:
                selected[(q, r)] = tile

        if not selected:
            # nothing selected — return an empty transparent image small enough to display
            return Image.new("RGBA", (int(HEX_SIZE), int(HEX_SIZE)))

        # compute pixel positions for every selected tile using a consistent formula
        # we'll use axial_to_pixel with an arbitrary r baseline (0), and then shift by min_x/min_y
        def axial_to_pixel_raw(q, r, q_origin):
            # raw pixel coords (floating) using q_origin to make x small
            x = HEX_SIZE * (1.5 * (q - q_origin))
            y = HEX_SIZE * (math.sqrt(3)/2 * (q - q_origin) + math.sqrt(3) * r)
            return x, y

        # choose q_origin = q_min to keep numbers small
        q_origin = q_min

        pixels = {}
        min_x = float("inf")
        min_y = float("inf")
        max_x = -float("inf")
        max_y = -float("inf")

        for (q, r), tile in selected.items():
            px, py = axial_to_pixel_raw(q, r, q_origin)
            # tile sprite likely has its own origin; if your sprites are anchored so the hex center
            # is at (0,0) in the sprite, you may need additional offsets here.
            pixels[(q, r)] = (px, py)
            min_x = min(min_x, px)
            min_y = min(min_y, py)
            max_x = max(max_x, px + terrain_sprites[tile.terrain.removesuffix("_coast")].width)
            max_y = max(max_y, py + terrain_sprites[tile.terrain.removesuffix("_coast")].height)

        # include padding
        min_x -= padding
        min_y -= padding
        max_x += padding
        max_y += padding

        width_px  = int(math.ceil(max_x - min_x))
        height_px = int(math.ceil(max_y - min_y))

        output = Image.new("RGBA", (width_px, height_px))

        # paste each tile offset by (-min_x, -min_y)
        for (q, r), tile in selected.items():
            px, py = pixels[(q, r)]
            paste_x = int(round(px - min_x))
            paste_y = int(round(py - min_y))
            terrain_img = terrain_sprites[tile.terrain.removesuffix("_coast")]
            output.paste(terrain_img, (paste_x, paste_y), terrain_img)

            if isinstance(tile, City):
                city_tier = tier_names[tile.tier]
                overlay_img = overlay_sprites[city_tier]
                output.paste(overlay_img, (paste_x, paste_y), overlay_img)
        return output

    except Exception as e:
        logger.error(f"Failed to render map: {e}")
        return None