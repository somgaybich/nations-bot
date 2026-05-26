from typing import TYPE_CHECKING

from game.constants import empty_inventory

import scripts.database as db

from world.world import tile_list, structures

if TYPE_CHECKING:
    from world.structures import Structure

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
    inventory: dict[str, float]
    """
    The amounts of each resource in this region. See the structure of 
    constants.empty_inventory for the guaranteed keys.
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
                 city_tier: int = 0, inventory: dict[str, float] | None = None, 
                 is_capital: bool = False, 
                 tiles: list[tuple[int, int]] = None):
        """
        :param name: The name of the central city of the region, and also the 
            region itself.
        :param location: The location of this region's central city.
        :param owner: The NID of the nation that controls this region.
        :param city_tier: The tier of this region's central city. Starts 
            at 0 and ranges to 4.
        :param inventory: The resources available to this region.
        :param is_capital: Whether this region is the capital of its nation.
        :param tiles: The list of tile coordinates that belong to this region.
        :type name: str
        :type location: tuple[int, int]
        :type owner: int
        :type city_tier: int
        :type stability: int
        :type authority: str
        :type is_capital: bool
        :type tiles: list[tuple[int, int]],
        :type inventory: dict[str, float]
        """
        self.name = name
        self.location = location
        self.owner = owner
        self.is_capital = is_capital
        self.city_tier = city_tier
        self.tiles = (tiles if tiles is not None 
                      else [tile.location for tile in tile_list[location].area()])
        self.inventory = (inventory if inventory is not None 
                          else empty_inventory)

    async def save(self):
        """
        Saves this region to the database.
        """
        await db.save_region(self)

    def structures(self) -> list["Structure"]:
        """
        Returns a list of every structure in this region.
        """
        city_structures = []
        for structure in structures:
            if structure.region == self.name:
                city_structures.append(structure)
        return city_structures

    def calculate_tier(self) -> int:
        """
        Used to calculate the new tier of a city. Will always return the
        current tier if it is 0 or 1.
        """ 
        #FIXME
        pass