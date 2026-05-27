from PIL import Image
import logging

from world.world import tile_list, nation_list, regions

logger = logging.getLogger(__name__)

HEX_WIDTH = 78.7
HEX_HEIGHT = 68.22
 
ANCHOR_Q = -65
ANCHOR_R = -8

source_image = Image.open("assets/map.png").convert("RGBA")

overlay_sprites = {
    "outpost": Image.open("assets/overlays/outpost.png").convert("RGBA"),
    "village": Image.open("assets/overlays/village.png").convert("RGBA"),
    "town": Image.open("assets/overlays/town.png").convert("RGBA"),
    "city": Image.open("assets/overlays/city.png").convert("RGBA"),
    "metropolis": Image.open("assets/overlays/metropolis.png").convert("RGBA"),
    "hex_mask": Image.open("assets/overlays/hex_mask.png").convert("RGBA").getchannel("A")
}

def n_corner(q, r) -> tuple[int, int]:
    """
    Finds the n-corner (top left) in rectangular image coordinates of a hex 
    given axial coordinates.
    """
    return (
        3/4 * HEX_WIDTH * (q - ANCHOR_Q),
        1/2 * HEX_HEIGHT * (q - ANCHOR_Q) + HEX_HEIGHT * (r - ANCHOR_R))

def m_corner(q, r) -> tuple[int, int]:
    """
    Finds the m-corner (bottom right) in rectangular image coordinates of a hex 
    given axial coordinates.
    """
    return (
        3/4 * HEX_WIDTH * (q - ANCHOR_Q + 1) + 1/4 * HEX_WIDTH,
        1/2 * HEX_HEIGHT * (q - ANCHOR_Q + 2) + HEX_HEIGHT * (r - ANCHOR_R)
    )

def snapshot_corners(corner1: tuple[int, int], corner2: tuple[int, int], 
                     overlays: dict[tuple[int, int], str] = {}) -> Image.Image:
    """
    Takes a rectangular snapshot of the source image based on
    axial hex coordinates.
    
    :param corner1: The (q, r) coordinates of the top-left cell in the image.
    :param corner2: The (q, r) coordinates ot the bottom-right cell in the 
        image.
    :param overlays: A set of custom sprites to overlay onto the map. The keys
        are the (q, r) coordinates of the cell to overlay onto, and the values
        are the names of the corresponding structures.
    :type corner1: tuple[int, int]
    :type corner2: tuple[int, int]
    :type overlays: dict[tuple[int, int], str]
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
        # The coordinates of the sprite on the cropped map
        box=(int(n_x - x_min), int(n_y - y_min))

        if x_min <= n_x and x_max >= m_x and y_min <= n_y and y_max >= m_y:
            # The tile's corners are in the snapshot bounds
            # Half-represented tiles don't get overlays
            if tile.owner != None:
                nid = regions[tile.owner].owner
                mask = overlay_sprites["hex_mask"]
                snapshot.paste(
                    im=nation_list[nid].color.to_rgb(),
                    box=box,
                    mask=mask
                )
            
            # Allows for custom overlays in specific locations
            if location in overlays.keys():
                sprite = overlay_sprites[overlays[location]]
                snapshot.paste(
                    im=sprite,
                    box=box,
                    mask=sprite
                )
            
    return snapshot

def snapshot_center(q, r, overlays: dict = {}) -> Image.Image:
    """
    Takes a single hex coordinate and takes a screenshot of the area q +- 5, 
    r +- 1 around that hex
    """
    return snapshot_corners((q-5, r-1), (q+5, r+1), overlays)