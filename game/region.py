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
    The tier of this region's central city. Starts at 0 and ranges to 4.
    """
    stability: int
    """
    (Soon to be deprecated) The stability of this region.
    """
    inventory: list["Resource"]
    """
    The resources in this region.
    """
    authority: str
    """
    The name of the authority that controls this region.
    """
    is_capital: bool
    """
    Whether this region is the capital of its nation.
    """
    infrastructure: int
    """
    The quality of this region's infrastructure. Used by the Region.max_trades
    function to calculate the maximum number of trades this region can handle.
    """
    trades: int
    """
    The total number of exports and imports to this region.
    """
    tiles: list[tuple[int, int]]
    """
    The list of tile coordinates that belong to this region.
    """
    def __init__(self, name: str, location: tuple[int, int], owner: int, 
                 city_tier: int = 0, stability: int = 80, 
                 inventory: list["Resource"] = None, authority: str = None,
                 is_capital: bool = False, infrastructure: int = 2,
                 trades: int = 0, tiles: list[tuple[int, int]] = None):
        """
        :param name: The name of the central city of the region, and also the 
            region itself.
        :param location: The location of this region's central city.
        :param owner: The NID of the nation that controls this region.
        :param city_tier: The tier of this region's central city. Starts 
            at 0 and ranges to 4.
        :param stability: (Soon to be deprecated) The stability of this region.
            Defaults to 80, on a scale from 0-100.
        :param inventory: The resources available to this region.
        :param authority: The name of the authority that controls this region.
        :param is_capital: Whether this region is the capital of its nation.
        :param infrastructure: The quality of this region's infrastructure. 
            Used by the Region.max_trades function to calculate the maximum 
            number of trades this region can handle.
        :param trades: The total number of exports and imports to this region.
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
        :type infrastructure: int
        :type trades: int
        """
        self.name = name
        self.location = location
        self.owner = owner
        self.is_capital = is_capital
        self.city_tier = city_tier
        self.stability = stability
        self.infrastructure = infrastructure
        self.trades = trades
        self.tiles = tiles if tiles is not None else [tile.location for tile in tile_list[location].area()]
        self.inventory = inventory if inventory is not None else []
        self.authority = (authority if authority is not None 
                          else nation_list[owner].name)

    async def save(self):
        """
        Saves this region to the database.
        """
        await db.save_region(self)

    def max_trades(self):
        """
        Gives the maximum number of imports and exports this region can handle.
        """
        return self.city_tier + self.infrastructure

    def find_resources(self, resource_name: str) -> list["Resource"]:
        """
        Returns a list of all unused instances of a specified resource type in 
        the region's raw inventory. If there is no matching resource, returns 
        an empty list.
        
        :param resource_name: The name of the resource to search for.
        """
        return [resource for resource in self.inventory 
                if resource.name == resource_name]

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
        return resource in [resource.name for resource in self.inventory]

    def calculate_tier(self) -> int:
        """
        Used to calculate the new tier of a city. This will always return the
        current tier if it is 0 or 1.
        """ 
        if self.city_tier < 2:
            # If the tier is less than 2, it won't be affected by luxuries.
            return self.city_tier

        if len(self.inventory) < 2:
            return 2
        elif len(self.inventory) < 5:
            return 3
        else:
            return 4