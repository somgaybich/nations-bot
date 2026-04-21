import logging
import json
from typing import TYPE_CHECKING

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from world.structures import Structure, Link

from game.constants import arable_biomes, dry_biomes, link_difficulties

import scripts.database as db

from world.world import tile_list

class Terrain:
    def __init__(self, biome: str, is_land: bool, is_water: bool, 
                 difficulty: int, straits: list | None = None):
        self.biome = biome
        self.is_land = is_land
        self.is_water = is_water
        self.difficulty = difficulty
        self.straits = straits if not straits is None else []
    
    def data(self):
        return json.dumps([self.biome, self.is_land, self.is_water, 
                           self.difficulty, self.straits])

class Tile:
    def __init__(self, terrain: Terrain, location: tuple[int, int] = (0, 0), 
                 owner: int = None, owned: bool = False, 
                 structure: "Structure" = None, 
                 link_structures: list["Link"] = None):
        self.terrain = terrain
        self.location = location
        self.owned = owned
        self.owner = owner
        self.structure = structure if structure is not None else {}
        self.link_structures = (link_structures if link_structures is not None 
                                else [])

        # The smallest link difficulty will become the tile difficulty, without one the terrain difficulty is used
        values = (link_difficulties.get(link.linktype.fname) for link in link_structures)
        self.difficulty = min(values, default=self.terrain.difficulty)

    async def save(self):
        await db.save_tile(self)
    
    def n(self) -> "Tile":
        return tile_list[(self.location[0], self.location[1] - 1)]

    def nw(self) -> "Tile":
        return tile_list[(self.location[0] - 1, self.location[1])]

    def sw(self) -> "Tile":
        return tile_list[(self.location[0] - 1, self.location[1] + 1)]

    def s(self) -> "Tile":
        return tile_list[(self.location[0], self.location[1] + 1)]

    def ne(self) -> "Tile":
        return tile_list[(self.location[0] + 1, self.location[1] - 1)]

    def se(self) -> "Tile":
        return tile_list[(self.location[0] + 1, self.location[1])]

    def area(self) -> list["Tile"]:
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
        result = set()
        for tile in self.area():
            result |= tile.area()
        return result

    def direction_to(self, target: "Tile") -> str | None:
        """
        Takes a tile and returns the name of the direction to that tile.
        If there is no direct path, returns None.
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

    def is_arable(self) -> bool:
        """
        Checks whether a tile meets the requirements for arability.
        """
        if self.terrain.biome in arable_biomes:
            return True

        if self.terrain.biome not in dry_biomes:
            # Tile isn't in arable or dry biomes
            # This tile cannot be arable
            return False

        # But if it is dry, it can be arable if it's given water...
        if self.is_coastal():
            return True
        for area_tile in self.area():
            if area_tile.structure == "Aqueduct":
                return True

        # This tile satisfies none of the conditions
        return False

    def is_coastal(self) -> bool:
        """
        Returns True if self.terrain.is_water and self.terrain.is_land.
        """
        if self.terrain.is_water and self.terrain.is_land:
            return True
        else:
            return False
        
def move_in_direction(current_tile: Tile, direction: str) -> tuple[Tile, Tile]:
    last_tile = current_tile
    new_tile: Tile = getattr(current_tile, direction)()

    return new_tile, last_tile

def hex_distance(a: Tile | tuple[int, int], b: Tile | tuple[int, int]) -> int:
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