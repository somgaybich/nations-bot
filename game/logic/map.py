from typing import TYPE_CHECKING

from game.data.constants import biome_arability, coastal_arability_factor

if TYPE_CHECKING:
    from game.objs.tile import Tile
    from game.objs.nation import Nation
    from game.objs.region import Region
    from game.objs.structure import Structure
    from world.world import GameState

def n(tile: "Tile", state: "GameState") -> "Tile":
    """
    Returns the tile North of the target.
    """
    return state.tiles[(tile.location[0], tile.location[1] - 1)]

def nw(tile: "Tile", state: "GameState") -> "Tile":
    """
    Returns the tile Northwest of the target.
    """
    return state.tiles[(tile.location[0] - 1, tile.location[1])]

def sw(tile: "Tile", state: "GameState") -> "Tile":
    
    """
    Returns the tile Southwest of the target.
    """
    return state.tiles[(tile.location[0] - 1, tile.location[1] + 1)]

def s(tile: "Tile", state: "GameState") -> "Tile":
    """
    Returns the tile South of the target.
    """
    return state.tiles[(tile.location[0], tile.location[1] + 1)]

def ne(tile: "Tile", state: "GameState") -> "Tile":
    """
    Returns the tile Northeast of the target.
    """
    return state.tiles[(tile.location[0] + 1, tile.location[1] - 1)]

def se(tile: "Tile", state: "GameState") -> "Tile":
    """
    Returns the tile Southeast of the target.
    """
    return state.tiles[(tile.location[0] + 1, tile.location[1])]

def get_area(tile: "Tile", state: "GameState") -> list["Tile"]:
    """
    Returns all the tiles that directly border the target.
    """
    area = set([tile.location])
    for fn in (n, nw, ne, s, sw, se):
        try:
            area_tile = fn(tile, state)
            if area_tile is not None:
                area.add(area_tile.location)
        except:
            pass
    return [state.tiles[location] for location in area]

def get_metroarea(tile: "Tile", state: "GameState") -> list["Tile"]:
    """
    Returns all the tiles within two of the target.
    """
    result = set()
    for area_tile in get_area(tile, state):
        result.update(get_area(area_tile, state))
    return list(result)

def neighbors(region: "Region", state: "GameState") -> list[int]:
    """
    Returns a list of the IDs of the regions that border the target region.
    """
    neighbors = set()

    for location in region.tiles:
        tile = state.tiles[location]
        for neighbor_tile in get_area(tile, state):
            if neighbor_tile.location in region.tiles:
                # Ignore our own tiles
                continue

            neighbors.add(tile.owner)
    
    return list(neighbors)

def get_direction_to(source: "Tile", target: "Tile") -> str | None:
    """
    Returns the lowercase name of the direction from the source tile to the
    target tile. If there is no direct path, returns None.
    """
    q, r = target.location
    
    difference_tuple = (q - source.location[0], r - source.location[1])
    if (not -1 < difference_tuple[0] < 1 
        or not -1 < difference_tuple[1] < 1):
        return None

    match difference_tuple:
        case (-1, 0):
            return "nw"
        case (0, -1):
            return "n"
        case (1, 1):
            return "ne"
        case (1, 0):
            return "se"
        case (0, 1):
            return "s"
        case (-1, 1):
            return "sw"

def tile_arability(tile: "Tile") -> float:
    """
    Returns the arability value for the target tile, based on biome and whether
    the tile is coastal. Used for calculating food production.
    """
    arability = biome_arability.__getattribute__(tile.terrain.biome)
    if is_coastal(tile):
        arability += coastal_arability_factor / arability**2
    
    return arability

def region_arability(region: "Region", state: "GameState") -> float:
    """
    Returns the sum arability of the target region's tiles. See 
    :class:`tile_arability`.
    """
    region_arability = 0
    for location in region.tiles:
        tile = state.tiles[location]
        region_arability += tile_arability(tile)
    return region_arability

def is_coastal(tile: "Tile") -> bool:
    """
    Returns True if tile.terrain.is_water and tile.terrain.is_land.
    """
    if tile.terrain.is_water and tile.terrain.is_land:
        return True
    else:
        return False

def has_port(region: "Region", state: "GameState") -> bool:
    """
    Returns True if the target region's core city is coastal.
    """
    return is_coastal(state.tiles[region.location])

def nation_capital(nation: "Nation", state: "GameState") -> "Region":
    """
    Returns this nation's capital region.
    """
    for region_id in nation.regions:
        region = state.regions[region_id]
        if region.is_capital:
            return region

def region_structures(region: "Region", state: "GameState") -> list["Structure"]:
    """
    Returns a list of every structure in the target region.
    """
    city_structures = []
    for location in region.tiles:
        tile = state.tiles[location]
        if tile.structure == None:
            continue

        city_structures.append(tile.structure)
    return city_structures

def move_in_direction(current_tile: "Tile", direction: str, state: "GameState") -> tuple["Tile", "Tile"]:
    """
    An undo-safe function for fetching tiles based on direction. Used in cases
    where the user is manually moving something. Returns a tuple of the new
    tile moved to and the previous tile. Does not actually move anything.

    :param current_tile: The tile where the target currently is.
    :param direction: The name of the direction ot move, in lowercase form.
    :type current_tile: Tile
    :type direction: str
    """
    last_tile = current_tile
    direction_function = globals().get(direction)
    new_tile: Tile = direction_function(current_tile, state)

    return new_tile, last_tile

def hex_distance(a: "Tile | tuple[int, int]", b: "Tile | tuple[int, int]") -> int:
    """
    Finds the distance between two tiles.
    """
    if isinstance(a, Tile):
        aq, ar = a.location
    else:
        aq, ar = a[0], a[1]
    
    if isinstance(b, Tile):
        bq, br = b.location
    else:
        bq, br = b[0], b[1]
    
    bq, br = b.location
    return (abs(aq - bq)
          + abs(aq + ar - bq - br)
          + abs(ar - br)) // 2