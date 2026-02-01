import logging

logger = logging.getLogger(__name__)

import scripts.database as db

from world.map import Tile
from world.structures import StructureList
from world.world import nation_list

class City(Tile):
    def __init__(self, terrain: str, name: str, influence: int = 0, tier: int = 0, location: tuple[int, int] = (0, 0), 
                 owner: int = None, structures: StructureList = StructureList(), 
                 stability: int = 80, inventory: list[str] = [], authority: str = None):
        super().__init__(terrain, location, owner, True, structures)
        self.name = name
        self.influence = influence
        self.tier = tier
        self.stability = stability
        self.inventory = inventory
        
        if authority == None:
            self.authority = nation_list[owner].name
        else:
            self.authority = authority

    async def save(self):
        await db.save_city(self)
        await db.save_tile(self)
    
    def luxury_count(self) -> int:
        luxuries = []
        for item in self.inventory:
            if item.startswith("luxurygoods") and item not in luxuries:
                luxuries.append(item)
        return len(luxuries)

    def developed_area(self) -> list[Tile]:
        if self.tier == 4:
            return self.metroarea()
        else:
            return self.area()

    def calculate_tier(self) -> int:
        inventory = self.inventory
        raw_inventory = [item.split("_")[0] for item in inventory]
        
        if "lumber" in inventory and "food" in inventory:
            if "lumber" in inventory and "fuel" in inventory and raw_inventory.count("food") >= 2:
                if raw_inventory.count("lumber") >= 2 and raw_inventory.count("food") >= 3 and raw_inventory.count("fuel") >= 2 and self.luxury_count() >= 1:
                    if raw_inventory.count("lumber") >= 3 and raw_inventory.count("food") >= 5 and raw_inventory.count("fuel") >= 3 and self.luxury_count() >= 2:
                        return 4
                    return 3
                return 2
            return 1
        else:
            return 0