from typing import TYPE_CHECKING

from data.constants import (food_surplus_use_rate, 
                            food_shortage_contract_rate)

import world.database as db

from game.logic.map import area, is_coastal, arability

if TYPE_CHECKING:
    from game.objs.structure import Structure
    from world.world import GameState

class Region:
    """
    A region including a central ctiy and a mutable group of tiles around it.
    Effectively the true unit of land.
    """
    name: str
    """
    The name of the central city of the region, and also the region itself.
    """
    id: int | None
    """
    The database ID of this region.
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
    The tier of this region's central city. Starts at 0 and ranges to 4. Based
    on population.
    """
    population: float
    """
    A measure of the size of this region's central city. Growth is based on
    surplus of needed resources. Not an actual population count, can be thought
    of as "the amount of people that consume x units of food."
    """
    is_capital: bool
    """
    Whether this region is the capital of its nation.
    """
    tiles: list[tuple[int, int]]
    """
    The list of tile coordinates that belong to this region.
    """
    market: int | None
    """
    The ID of the market this region belongs to. Can occasionally be None only 
    if markets are currently being rebuilt.
    """
    industries: list[str]
    """
    The industries in this region. See :class:`game.industry.IndustryType`
    """
    def __init__(self, name: str, location: tuple[int, int], owner: int, 
                 state: "GameState", city_tier: int = 0, 
                 is_capital: bool = False, population: float = 1.0, 
                 tiles: list[tuple[int, int]] | None = None, 
                 industries: list[str] | None = None, id: int | None = None):
        """
        :param name: The name of the central city of the region, and also the 
            region itself.
        :param location: The location of this region's central city.
        :param owner: The NID of the class nation that controls this region.
        :param city_tier: The tier of this region's central city. Starts 
            at 0 and ranges to 4.
        :param is_capital: Whether this region is the capital of its nation.
        :param population: A measure of the size of this region's central city.
            Growth is based on surplus of needed resources. Not an actual 
            population count, can be thought of as "the amount of people that 
            consume x units of food."
        :param tiles: The list of tile coordinates that belong to this region.
        :param industries: The names of industries in this region. See 
            :class:`game.industry.industry_types`
        :type name: str
        :type location: tuple[int, int]
        :type owner: int
        :type city_tier: int
        :type is_capital: bool
        :type tiles: list[tuple[int, int]]
        :type industries: list["IndustryType"]
        """
        self.name = name
        self.location = location
        self.owner = owner
        self.is_capital = is_capital
        self.city_tier = city_tier
        self.population = population
        self.tiles = (tiles if tiles is not None 
                      else [tile.location for tile in area(state.tiles[location], state)])
        self.industries = (industries if industries is not None
                           else [])
        self.id = id
        self.market = None

    async def save(self):
        """
        Saves this region to the database.
        """
        await db.save_region(self)

    def growth(self, state: "GameState"):
        """
        Returns the amount the population of this region will grow according
        to the current supplies in the market.
        """
        market = state.markets[self.market]
        regions = len(market.regions)
        available_food = market.supply("food")
        # We'll use some % of our surplus
        growth_rate = available_food / regions * food_surplus_use_rate
        if growth_rate < 0:
            # If we have a shortage, we should shrink slower
            growth_rate *= food_shortage_contract_rate
        
        # FIXME: Incorporate other resources based on tier

        return growth_rate

    def structures(self, state: "GameState") -> list["Structure"]:
        """
        Returns a list of every structure in this region.
        """
        city_structures = []
        for location in self.tiles:
            tile = state.tiles[location]
            if tile.structure == None:
                continue

            city_structures.append(tile.structure)
        return city_structures

    def calculate_tier(self) -> int:
        """
        Calculates the new tier of a city.
        """ 
        #FIXME
        pass

    def connected(self, target: int, state: "GameState") -> bool:
        """
        Returns True if this region has a direct connection to the region with
        the target ID. Used for trading.
        """
        target_region = state.regions[target]
        
        if target in self.neighbors():
            return True
        
        if self.has_port() and target_region.has_port():
            return True
        
        return False

    def neighbors(self, state: "GameState") -> list[int]:
        """
        Returns a list of all the regions that border this one.
        """
        neighbors = set()

        for location in self.tiles:
            tile = state.tiles[location]
            for neighbor_tile in area(tile, state):
                if neighbor_tile.location in self.tiles:
                    # Ignore our own tiles
                    continue

                neighbors.add(tile.owner)
        
        return list(neighbors)

    def has_port(self, state: "GameState") -> bool:
        """
        Returns True if this region's core city is coastal.
        """
        return is_coastal(state.tiles[self.location])
    
    def arability(self, state: "GameState") -> float:
        """
        Returns the sum arability of the region's tiles. See 
        :class:`world.map.Tile.arability`.
        """
        region_arability = 0
        for location in self.tiles:
            tile = state.tiles[location]
            region_arability += arability(tile)
        return region_arability