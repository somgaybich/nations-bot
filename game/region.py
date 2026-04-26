from typing import TYPE_CHECKING

import scripts.database as db

from world.world import tile_list, structures, nation_list

if TYPE_CHECKING:
    from game.resources import Resource
    from world.map import Tile
    from world.structures import Structure, StructureType

class Region():
    """
    A region including a central ctiy and a mutable group of tiles around it.
    Effectively the true unit of land.
    """
    name: str
    """
    The name of the central city of the region, and also the region itself.
    """
    location: tuple[int, int]
    """
    The location of this region's central city.
    """
    owner: int
    """
    The NID of the nation that controls this region.
    """
    city_tier: int
    """
    The tier of this region's central city.
    """
    stability: int
    """
    (Soon to be deprecated) The stability of this region.
    """
    inventory: list["Resource"]
    """
    The resources available to this region.
    """
    authority: str
    """
    The name of the authority that controls this region.
    """
    is_capital: bool
    """
    Whether this region is the capital of its nation.
    """
    tiles: list[tuple[int, int]]
    """
    The list of tile coordinates that belong to this region.
    """
    def __init__(self, name: str, location: tuple[int, int], owner: int, 
                 city_tier: int = 0, stability: int = 80, 
                 inventory: list["Resource"] = None, authority: str = None,
                 is_capital: bool = False, 
                 tiles: list[tuple[int, int]] = None):
        """
        :param name: The name of the central city of the region, and also the 
            region itself.
        :param location: The location of this region's central city.
        :param owner: The NID of the nation that controls this region.
        :param city_tier: The tier of this region's central city. Starts at 0
            and ticks upward to 4.
        :param stability: (Soon to be deprecated) The stability of this region.
            Defaults to 80, on a scale from 0-100.
        :param inventory: The resources available to this region.
        :param authority: The name of the authority that controls this region.
        :param is_capital: Whether this region is the capital of its nation.
        :param tiles: The list of tile coordinates that belong to this region.
        :type name: str
        :type location: tuple[int, int]
        :type owner: int
        :type city_tier: int
        :type stability: int
        :type inventory: list[Resource]
        :type authority: str
        :type is_capital: bool
        :type tiles: list[tuple[int, int]]
        """
        self.name = name
        self.location = location
        self.owner = owner
        self.is_capital = is_capital
        self.city_tier = city_tier
        self.stability = stability
        self.tiles = tiles if tiles is not None else [tile.location for tile in tile_list[location].area()]
        self.inventory = inventory if inventory is not None else []
        self.authority = (authority if authority is not None 
                          else nation_list[owner].name)

    async def save(self):
        """
        Saves this region to the database.
        """
        await db.save_region(self)

    def find_resources(self, resource_name: str) -> list["Resource"]:
        """
        Returns a list of all unused instances of a specified resource type in 
        the region's raw inventory. If there is no matching resource, returns 
        an empty list.
        
        :param resource_name: The name of the resource to search for. Is
            subtype sensitive if a subtype name is provided, i.e. 
            Region.find_resource("food") will return a "food_meat" item but 
            Region.find_resource("food_grain") will not.
        """
        results = set()
        if "_" in resource_name:
            # This query specifies a subtype 
            for item in self.inventory:
                if (item.name == resource_name 
                    and item.used_in is None):
                    results.add(item)
        else:
            for item in self.inventory:
                if (item.name.split("_")[0] == resource_name
                    and item.used_in is None):
                    results.add(item)
        
        return list(results)

    def raw_inventory(self) -> list[str]:
        """
        Returns the list of names of resources in a region. Cleaves subtype 
        specifiers.
        """
        return [item.name.split("_")[0] for item in self.inventory]

    def luxury_count(self) -> int:
        """
        Returns the number of unique luxury types in the region's inventory.
        """
        luxuries = []
        for item in self.inventory:
            if item.name.startswith("luxurygoods") and item not in luxuries:
                luxuries.append(item)
        return len(luxuries)

    def developed_area(self) -> list["Tile"]:
        """
        Returns all tiles in the region's developed area, the area around the
        city where urban structures can be built.
        """
        if self.city_tier == 4:
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
        Returns a list of every unique structure type bound to this region.
        """
        return list(set([structure.structure_type.fname 
                         for structure in self.structures()]))

    def has_resource(self, resource: str) -> bool:
        """
        Returns true if this region has a resource with the specified name. Is
        subtype sensitive only if a subtype specifier is used.
        """
        if "_" in resource:
            # This query specifies a subtype
            return resource in [resource.name for resource in self.inventory]
        else:
            return resource in self.raw_inventory()

    def calculate_tier(self) -> int:
        """
        Used to calculate the new tier of a region after each season. Does not
        bind or save the new value.
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