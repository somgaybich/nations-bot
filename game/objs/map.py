import logging
import json
from typing import TYPE_CHECKING

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from game.objs.structures import Structure

from data.constants import biome_arability, coastal_arability_factor

import world.database as db

from world.world import tile_list

class Terrain:
    """
    Holds the terrain data of a particular tile.
    """
    biome: str
    """
    The climate biome of the parent tile.
    """
    is_land: bool
    """
    Whether this tile is land or not.
    """
    is_water: bool
    """
    Whether this tile is water or not.
    """
    difficulty: int
    """
    The amount of free movement a unit loses for passing through this tile.
    """
    straits: list[int]
    """
    Any straits that might be adjacent to this tile. Corresponds to a side of 
    this tile counting counterclockwise starting from the NE side with index 0.
    """
    ores: dict[str, float]
    """
    The richnesses of ores in this tile. Has keys "iron", "copper", "gold", and
    "coal", "oil".
    """
    def __init__(self, biome: str, is_land: bool, is_water: bool, 
                 difficulty: int, straits: list[int] | None = None,
                 ores: dict[str, float] | None = None):
        """
        :param biome: The climate biome of the parent tile.
        :param is_land: Whether this tile is land or not.
        :param is_water: Whether this tile is water or not.
        :param difficulty: The amount of free movement a unit loses for passing
            through this tile.
        :param straits: Any straits that might be adjacent to this tile. 
            Corresponds to a side of this tile counting counterclockwise 
            starting from the NE side with index 0.
        :type biome: str
        :type is_land: bool
        :type is_water: bool
        :type difficulty: int
        :type straits: list[int] | None
        """
        self.biome = biome
        self.is_land = is_land
        self.is_water = is_water
        self.difficulty = difficulty
        self.straits = straits if not straits is None else []
        self.ores = ores if not ores is None else {}
    
    def data(self):
        """
        Returns a json-safe version of this terrain data to be saved
        in the database.
        """
        return json.dumps([self.biome, self.is_land, self.is_water, 
                           self.difficulty, self.straits, self.ores])

class Tile:
    """
    A tile on the game map.
    """
    terrain: Terrain
    """
    A terrain object that corresponds to this tile's physical conditions.
    """
    location: tuple[int, int]
    """
    The (q, r) axial coordinates of this tile on the game map.
    """
    owner: str | None
    """
    The name of the region that owns this tile, if any.
    """
    structure: "Structure | None"
    """
    The player-built object on this tile.
    """
    def __init__(self, terrain: Terrain, location: tuple[int, int] = (0, 0), 
                 owner: str = None, structure: "Structure" = None):
        """
        :param terrain: A terrain object that contains the tile's physical 
            conditions.
        :param location: The (q, r) axial coordinates of this tile on the game 
            map.
        :param owner: The name of the region that owns this tile, if any.
        :param structure: The player-built object on this tile.
        :type terrain: Terrain
        :type location: tuple[int, int]
        :type owner: str
        :type structure: Structure
        """
        self.terrain = terrain
        self.location = location
        self.owner = owner
        self.structure = structure

        # tile difficulty adjustment based on region infrastructure level?
        self.difficulty = self.terrain.difficulty

    async def save(self):
        """
        Saves this tile to the database.
        """
        await db.save_tile(self)
    
    def n(self) -> "Tile":
        """
        Returns the tile North of this one.
        """
        return tile_list[(self.location[0], self.location[1] - 1)]

    def nw(self) -> "Tile":
        """
        Returns the tile Northwest of this one.
        """
        return tile_list[(self.location[0] - 1, self.location[1])]

    def sw(self) -> "Tile":
        
        """
        Returns the tile Southwest of this one.
        """
        return tile_list[(self.location[0] - 1, self.location[1] + 1)]

    def s(self) -> "Tile":
        """
        Returns the tile South of this one.
        """
        return tile_list[(self.location[0], self.location[1] + 1)]

    def ne(self) -> "Tile":
        """
        Returns the tile Northeast of this one.
        """
        return tile_list[(self.location[0] + 1, self.location[1] - 1)]

    def se(self) -> "Tile":
        """
        Returns the tile Southeast of this one.
        """
        return tile_list[(self.location[0] + 1, self.location[1])]

    def area(self) -> list["Tile"]:
        """
        Returns all the tiles that directly border this one.
        """
        area = [self]
        for fn in (self.n, self.nw, self.sw, self.s, self.ne, self.se):
            try:
                tile = fn()
                if tile is not None:
                    area.append(tile)
            except:
                pass
        return set(area)

    def metroarea(self) -> set["Tile"]:
        """
        Returns all the tiles within two of this one.
        """
        result = set()
        for tile in self.area():
            result |= tile.area()
        return result

    def direction_to(self, target: "Tile") -> str | None:
        """
        Takes a tile and returns the lowercase name of the direction to that 
        tile. If there is no direct path, returns None.
        """
        q, r = target.location
        
        difference_tuple = (q - self.location[0], r - self.location[1])
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

    def arability(self) -> float:
        """
        Returns the arability value for this tile, based on biome and whether
        the tile is coastal. Used for calculating food production.
        """
        arability = biome_arability[self.terrain.biome]
        if self.is_coastal():
            arability += coastal_arability_factor / arability**2
        
        return arability

    def is_coastal(self) -> bool:
        """
        Returns True if self.terrain.is_water and self.terrain.is_land.
        """
        if self.terrain.is_water and self.terrain.is_land:
            return True
        else:
            return False
        
def move_in_direction(current_tile: Tile, direction: str) -> tuple[Tile, Tile]:
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
    new_tile: Tile = getattr(current_tile, direction)()

    return new_tile, last_tile

def hex_distance(a: Tile | tuple[int, int], b: Tile | tuple[int, int]) -> int:
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