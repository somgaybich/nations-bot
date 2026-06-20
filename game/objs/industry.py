import logging

logger = logging.getLogger(__name__)

from typing import Callable, TYPE_CHECKING
import math

from world.world import tile_list, markets

if TYPE_CHECKING:
    from game.objs.region import Region

class IndustryType:
    """
    Defines a type of industry that can be in a region.
    """
    cost: int
    """
    The influence cost of establishing this industry.
    """
    production: Callable[["Region"], tuple[str, float]]
    """
    A function that returns the resources produced by this industry. Takes
    the parent :class:`game.region.Region`, and returns a tuple where element 0
    is the name of the resource produced and element 1 is the amount.
    """
    def __init__(self, cost: int, 
                 production: Callable[[str], tuple[str, float]]):
        """
        Defines a type of industry that can be in a region.
        
        :param cost: The influence cost of establishing this industry.
        :param production: A function that returns the resources produced by 
            this industry. Takes the parent :class:`game.region.Region`, and 
            returns a tuple where element 0 is the name of the resource 
            produced and element 1 is the amount.
        :type cost: int
        :type production: Callable[[str], tuple[str, float]]
        """
        self.cost = cost
        self.production = production

def subsistence_production(region: "Region") -> tuple[str, float]:
    """
    Returns food equal to the sum of the arabilities of the region's tiles,
    see :class:`world.map.Tile.arability`. 
    """
    production = region.arability() / math.sqrt(region.population)
    if "textile" in region.industries:
        production *= 0.4
    return ("food", production)

def farming_production(region: "Region") -> tuple[str, float]:
    subsistence = subsistence_production(region)
    production = region.arability() * subsistence
    return ("food", production)

def mines_production(ore: str) -> Callable[[str], tuple[str, float]]:
    """
    Creates a mining production function for this industry based on the
    passed ore. Output is based on the sum of the richness values of the 
    region's tiles, see :class:`world.map.Terrain.ores`.
    """
    def mine_production(region: "Region") -> tuple[str, float]:
        base_production = 0
        for location in region.tiles:
            tile = tile_list[location]
            base_production += tile.terrain.ores[ore]
        
        production = base_production * region.population

        return (ore, production)

    return mine_production

def steel_production(region: "Region") -> tuple[str, float]:
    market = markets[region.market]
    iron_fill = market.fulfillment("iron")
    coal_fill = market.fulfillment("coal")
    limiter = min(iron_fill, coal_fill)
    production = limiter * region.population

    return ("steel", production)
    
def machinery_production(region: "Region") -> tuple[str, float]:
    market = markets[region.market]
    iron_fill = market.fulfillment("iron")
    copper_fill = market.fulfillment("copper")
    limiter = min(iron_fill, copper_fill)
    production = limiter * region.population

    return ("machinery", production)

def luxuries_production(luxury: str) -> Callable[[str], tuple[str, float]]:
    """
    Creates a luxury production function for this industry based on the passed
    luxury type. All luxury industries just produce 1 unit in ideal conditions.
    """
    def luxury_production(region: "Region") -> tuple[str, float]:
        return (luxury, region.population)
    
    return luxury_production

industry_types = {
    "subsistence": IndustryType(
        cost=0,
        production=subsistence_production
    ),
    "farming": IndustryType(
        cost=2,
        production=farming_production
    ),
    "iron_mining": IndustryType(
        cost=3,
        production=mines_production("iron")
    ),
    "copper_mining": IndustryType(
        cost=3,
        production=mines_production("copper")
    ),
    "gold_mining": IndustryType(
        cost=3,
        production=mines_production("gold")
    ),
    "coal_mining": IndustryType(
        cost=3,
        production=mines_production("coal")
    ),
    "oil_drilling": IndustryType(
        cost=4,
        production=mines_production("oil")
    ),
    "steelworks": IndustryType(
        cost=4,
        production=steel_production
    ),
    "foundry": IndustryType(
        cost=4,
        production=machinery_production
    ),
    "textile": IndustryType(
        cost=3,
        production=luxuries_production("textiles")
    ),
    "jewelry": IndustryType(
        cost=4,
        production=luxuries_production("jewelry")
    ),
    "spice": IndustryType(
        cost=4,
        production=luxuries_production("spice")
    ),
    "consumer_goods": IndustryType(
        cost=4,
        production=luxuries_production("consumer_goods")
    ),
    "horses": IndustryType(
        cost=4,
        production=luxuries_production("horses")
    ),
    "gems": IndustryType(
        cost=4,
        production=luxuries_production("gems")
    ),
    "glass": IndustryType(
        cost=4,
        production=luxuries_production("glass")
    )
}