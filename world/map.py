import logging
import json

logger = logging.getLogger(__name__)

import scripts.database as db

from world.structures import StructureList
from world.world import tile_list

class Terrain:
    def __init__(self, land_biome: str, water_biome: str, is_land: bool, is_water: bool, difficulty: int):
        self.land_biome = land_biome
        self.water_biome = water_biome
        self.is_land = is_land
        self.is_water = is_water
        self.difficulty = difficulty
    
    def data(self):
        return json.dumps([self.land_biome, self.water_biome, self.is_land, self.is_water])

class Tile:
    def __init__(self, terrain: Terrain, location: tuple[int, int] = (0, 0), owner: str = None, 
                 owned: bool = False, structures: StructureList = None):
        self.terrain = terrain
        self.location = location
        self.owned = owned
        self.owner = owner
        self.structures = structures if structures is not None else StructureList()

        if "simple_rail" in structures:
            self.difficulty = 0.5
        elif "quality_rail" in structures:
            self.difficulty = 0.25
        else:
            self.difficulty = terrain.difficulty
    
    async def save(self):
        await db.save_tile(self)
    
    def n(self) -> "Tile":
        return tile_list[(self.location[0], self.location[1] - 1)]

    def nw(self) -> "Tile":
        return tile_list[(self.location[0] - 1, self.location[1])]

    def sw(self) -> "Tile":
        return tile_list[(self.location[0] - 1, self.location[1] - 1)]

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

def move_in_direction(current_tile: Tile, direction: str) -> tuple[Tile, Tile]:
    last_tile = current_tile
    new_tile: Tile = getattr(current_tile, direction)()

    return new_tile, last_tile

def hex_distance(a: Tile, b: Tile) -> int:
    aq, ar = a.location
    bq, br = b.location
    return (abs(aq - bq)
          + abs(aq + ar - bq - br)
          + abs(ar - br)) // 2