from typing import TYPE_CHECKING

from game.constants import empty_inventory

import scripts.database as db

from world.world import tile_list, structures

if TYPE_CHECKING:
    from world.structures import Structure

class Region:
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
    is_capital: bool
    """
    Whether this region is the capital of its nation.
    """
    tiles: list[tuple[int, int]]
    """
    The list of tile coordinates that belong to this region.
    """
    market: str
    """
    The name of the market this region belongs to.
    """
    def __init__(self, name: str, location: tuple[int, int], owner: int, 
                 city_tier: int = 0, is_capital: bool = False, 
                 market: str | None = None,
                 tiles: list[tuple[int, int]] = None):
        """
        :param name: The name of the central city of the region, and also the 
            region itself.
        :param location: The location of this region's central city.
        :param owner: The NID of the class nation that controls this region.
        :param city_tier: The tier of this region's central city. Starts 
            at 0 and ranges to 4.
        :param is_capital: Whether this region is the capital of its nation.
        :param market: The name of the market this region belongs to.
        :param tiles: The list of tile coordinates that belong to this region.
        :type name: str
        :type location: tuple[int, int]
        :type owner: int
        :type city_tier: int
        :type is_capital: bool
        :type market: str
        :type tiles: list[tuple[int, int]],
        """
        self.name = name
        self.location = location
        self.owner = owner
        self.is_capital = is_capital
        self.city_tier = city_tier
        self.tiles = (tiles if tiles is not None 
                      else [tile.location for tile in tile_list[location].area()])
        
        if market is not None:
            self.market = market
        else:
            #FIXME join one!
            pass

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