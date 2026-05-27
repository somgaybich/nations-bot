from typing import TYPE_CHECKING

import scripts.database as db

from world.world import tile_list, structures, regions, markets

if TYPE_CHECKING:
    from game.market import Market
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
            # Will join a new market with itself as the only member
            # This market has to be separately instatiated for import safety
            self.market = name

    async def save(self):
        """
        Saves this region to the database.
        """
        await db.save_region(self)

    async def merge_markets(self):
        """
        Finds a connected :class:`Market` to join. This should generally only 
        be run once, when the region is first created.
        """
        current_market = markets[self.market]

        if self.has_port():
            # Find a port region owned by the same nation
            for region in regions.values():
                if region.has_port() and region.owner == self.owner:
                    # Join their market!
                    target_market = markets[region.market]
                    await target_market.merge_markets(current_market)
                    return
        
        # Find all connected markets
        neighbors = [regions[name] for name in self.neighbors()]

        if len(neighbors) == 0:
            # If there are none, we're done
            return

        connected_markets: set["Market"] = set()
        for neighbor in neighbors:
            if neighbor.owner != self.owner:
                # Ignore foreign markets
                continue

            connected_markets.add(markets[neighbor.market])
        
        # Merge them together
        primary_market = next(iter(connected_markets))
        for market in connected_markets:
            primary_market.merge_markets(market)

    async def supply_delta(self, item: str, amount: float):
        """
        Changes the supply of an item in this region's :class:`Market`.
        """
        market = markets[self.market]
        market.supply[item] += amount
        await market.save()

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
        Calculates the new tier of a city.
        """ 
        #FIXME
        pass

    def connected(self, target: str) -> bool:
        """
        Returns True if this region has a direct connection to the target
        region. Used for trading.
        """
        target_region = regions[target]
        
        if target in self.neighbors():
            return True
        
        if self.has_port() and target_region.has_port():
            return True
        
        return False

    def neighbors(self) -> list[str]:
        """
        Returns a list of all the regions that border this one.
        """
        neighbors = set()

        for location in self.tiles:
            tile = tile_list[location]
            for neighbor_tile in tile.area():
                if neighbor_tile.location in self.tiles:
                    # Ignore our own tiles
                    continue

                neighbors.add(tile.owner)
        
        return list(neighbor_tile)

    def has_port(self) -> bool:
        """
        Returns True if this region's core city is coastal.
        """
        return tile_list[self.location].is_coastal()
    
    def arability(self) -> float:
        """
        Determines the sum arability of a region. Just the sum of arability
        of the region's tiles, see :class:`world.map.Tile.arability`
        """
        arability = 0
        for location in self.tiles:
            tile = tile_list[location]
            arability += tile.arability()
        
        return arability

    
