from typing import TYPE_CHECKING

import scripts.database as db

from world.world import tile_list, structures, nation_list

if TYPE_CHECKING:
    from game.resources import Resource
    from world.map import Tile
    from world.structures import Structure, StructureType

class Region():
    def __init__(self, name: str, location: tuple[int, int], owner: int, 
                 tier: int = 0, stability: int = 80, 
                 inventory: list["Resource"] = None, authority: str = None,
                 is_capital: bool = False, 
                 tiles: list[tuple[int, int]] = None):
        # Center city info
        self.name = name # MUST BE UNIQUE (not currently checked)
        self.location = location
        # Regional info
        self.owner = owner
        self.is_capital = is_capital # Whether or not this is the capital
        self.tier = tier
        self.stability = stability
        self.tiles = tiles if tiles is not None else [tile.location for tile in tile_list[location].area()]
        self.inventory = inventory if inventory is not None else []
        self.authority = (authority if authority is not None 
                          else nation_list[owner].name)

    async def save(self):
        await db.save_region(self)

    def find_resource(self, resource_name: str) -> "Resource":
        """
        Returns an available resource in the region's inventory.
        If there's no matching resource, returns None.
        """
        for item in self.inventory:
            if (item.name == resource_name
                and item.used_in is None):
                return item
        
        # We weren't able to find a matching resource
        return None

    def raw_inventory(self) -> list[str]:
        """
        Returns the list of names of resources in a region.
        """
        return [item.name.split("_")[0] for item in self.inventory]

    def luxury_count(self) -> int:
        """
        Returns the number of unique luxuries in the region's inventory.
        """
        luxuries = []
        for item in self.inventory:
            if item.name.startswith("luxurygoods") and item not in luxuries:
                luxuries.append(item)
        return len(luxuries)

    def developed_area(self) -> list["Tile"]:
        """
        Returns all tiles in the region's developed area.
        """
        if self.tier == 4:
            return tile_list[self.location].metroarea()
        else:
            return tile_list[self.location].area()

    def structures(self) -> list["Structure"]:
        """
        Returns a list of every structure in this region.
        """
        city_structures = []
        for structure in structures:
            if structure.region == self.name:
                city_structures.append(structure)
        return city_structures

    def structure_types(self) -> list["StructureType"]:
        """
        Returns a list of every structure type bound to this region.
        Does not include duplicates.
        """
        return list(set([structure.structure_type.fname 
                         for structure in self.structures()]))

    def has_resource(self, resource: str) -> bool:
        """
        Returns true if this region has a resource with name 'resource.'
        Will not differentiate between subtypes.
        """
        return resource in self.raw_inventory()

    def calculate_tier(self) -> int:
        """
        Used to calculate the new tier of a region after each season.
        """ 
        raw_inventory = self.raw_inventory()
        
        if "lumber" in raw_inventory and "food" in raw_inventory:
            if ("lumber" in raw_inventory 
                and "fuel" in raw_inventory 
                and raw_inventory.count("food") >= 2):
                if (raw_inventory.count("lumber") >= 2 
                    and raw_inventory.count("food") >= 3 
                    and raw_inventory.count("fuel") >= 2 
                    and self.luxury_count() >= 1):
                    if (raw_inventory.count("lumber") >= 3 
                        and raw_inventory.count("food") >= 5 
                        and raw_inventory.count("fuel") >= 3 
                        and self.luxury_count() >= 2):
                        return 4
                    return 3
                return 2
            return 1
        else:
            return 0