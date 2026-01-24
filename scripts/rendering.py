from PIL import Image
import logging
from math import sqrt

from world.map import Tile
from world.cities import City
from world.world import tile_list, TileDict

logger = logging.getLogger(__name__)

HEX_WIDTH = 78.65
HEX_HEIGHT = 68.2
 
ANCHOR_Q = -65
ANCHOR_R = -8

source_image = Image.open("assets/map.png").convert("RGBA")

# TODO: Add other link types
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

def n_corner(q, r) -> tuple[int, int]:
    """
    Finds the n-corner (top left) in rectangular image coordinates of a hex given axial coordinates
    """
    return (
        3/4 * HEX_WIDTH * (q - ANCHOR_Q),
        1/2 * HEX_HEIGHT * (q - ANCHOR_Q) + HEX_HEIGHT * (r - ANCHOR_R))

def m_corner(q, r) -> tuple[int, int]:
    """
    Finds the m-corner (bottom right) in rectangular image coordinates of a hex given axial coordinates
    """
    return (
        3/4 * HEX_WIDTH * (q - ANCHOR_Q + 1) + 1/4 * HEX_WIDTH,
        1/2 * HEX_HEIGHT * (q - ANCHOR_Q + 2) + HEX_HEIGHT * (r - ANCHOR_R)
    )

def snapshot_corners(corner1, corner2) -> Image.Image:
    """
    Takes a rectangular snapshot of the source image based on
    axial hex coordinates.
    """

    q1, r1 = corner1
    q2, r2 = corner2

    x_min, y_min = n_corner(q1, r1)
    x_max, y_max = m_corner(q2, r2)

    snapshot = source_image.crop((x_min, y_min, x_max, y_max))

    for location, tile in tile_list.items():
        qt, rt = location

        n_x, n_y = n_corner(qt, rt)
        m_x, m_y = m_corner(qt, rt)
        # This is the bounds of the overlay sprite on the cropped map
        box=(int(n_x - x_min), int(n_y - y_min))

        # The tile's top-left corner and bottom-right corner are in the snapshot bounds
        # (Half-represented tiles, like those on the vertical edges, don't get overlays)
        if x_min <= n_x and x_max >= m_x and y_min <= n_y and y_max >= m_y:
            logger.info(f"{(qt, rt)} is in the range of the snapshot!")

            if tile.structures.has("Simple Rail"):
                for area_tile in tile.area():
                    if area_tile.structures.has("Simple Rail"):
                        direction = tile.direction_to(area_tile)
                        sprite = overlay_sprites["rail_" + direction]
                        snapshot.paste(
                            im=sprite,
                            box=box,
                            mask=sprite
                        )
            if tile.structures.has("Quality Rail"):
                for area_tile in tile.area():
                    if area_tile.structures.has("Quality Rail"):
                        direction = tile.direction_to(area_tile)
                        sprite = overlay_sprites["qrail_" + direction]
                        snapshot.paste(
                            im=sprite,
                            box=box,
                            mask=sprite
                        )
            if tile.structures.has("Stone Road"):
                for area_tile in tile.area():
                    if area_tile.structures.has("Stone Road"):
                        direction = tile.direction_to(area_tile)
                        sprite = overlay_sprites["road_" + direction]
                        snapshot.paste(
                            im=sprite,
                            box=box,
                            mask=sprite
                        )
            if tile.structures.has("Sea Route"):
                for area_tile in tile.area():
                    if area_tile.structures.has("Sea Route"):
                        direction = tile.direction_to(area_tile)
                        sprite = overlay_sprites["searoute_" + direction]
                        snapshot.paste(
                            im=sprite,
                            box=box,
                            mask=sprite
                        )

            if isinstance(tile, City):
                logger.info(f"{(qt, rt)} is a city!")
                sprite=overlay_sprites[tier_names[tile.tier]]
                snapshot.paste(
                    im=sprite,
                    box=box,
                    mask=sprite
                )
            
    return snapshot

def snapshot_center(hex: Tile | tuple[int, int]) -> Image.Image:
    """
    Takes a single hex coordinate and takes a screenshot of the area q +- 5, r +- 1 around that hex
    """
    if isinstance(hex, Tile):
        q, r = hex.location
    elif isinstance(hex, tuple) and isinstance(hex[0], int) and isinstance(hex[1], int):
        q, r = hex
    else:
        raise TypeError("Invalid snapshot center: Not a tile or coordinate")

    return snapshot_corners((q-5, r-1), (q+5, r+1))