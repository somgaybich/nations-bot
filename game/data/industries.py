import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

from typing import Callable, TYPE_CHECKING
import math

from game.data.constants import (textile_food_debuff, luxury_mult, 
                                 steel_mult, machine_mult)
from game.logic.map import region_arability
from game.logic.logistics import get_fulfillment

if TYPE_CHECKING:
    from game.objs.region import Region
    from world.world import GameState

@dataclass
class IndustryType:
    """
    Defines a type of industry that can be in a region.
    """
    cost: int
    """
    The influence cost of establishing this industry.
    """
    production: Callable[["Region", "GameState"], tuple[str, float]]
    """
    A function that returns the resources produced by this industry. Takes
    the parent :class:`Region` and the current :class:`GameState`, and 
    returns a tuple where element 0 is the name of the resource produced and 
    element 1 is the amount.
    """
    name: str
    """
    The name of the industry. Used in persistence, should always just be the
    key of the type in :class:`industry_types`.
    """

def subsistence_production(
        region: "Region", 
        state: "GameState"
    ) -> tuple[str, float]:
    """
    Returns food equal to the sum of the arabilities of the region's tiles,
    see :class:`world.map.Tile.arability`. 
    """
    production = region_arability(region, state) / math.sqrt(region.population)
    if "textile" in region.industries:
        production *= textile_food_debuff
    return ("food", production)

def farming_production(
        region: "Region", 
        state: "GameState"
    ) -> tuple[str, float]:
    subsistence = subsistence_production(region)
    production = region_arability(region, state) * subsistence
    return ("food", production)

def mines_production(
        ore: str
    ) -> Callable[[str], tuple[str, float]]:
    """
    Creates a mining production function for this industry based on the
    passed ore. Output is based on the sum of the richness values of the 
    region's tiles, see :class:`world.map.Terrain.ores`.
    """
    def mine_production(
            region: "Region", 
            state: "GameState"
        ) -> tuple[str, float]:
        base_production = 0
        for location in region.tiles:
            tile = state.tiles[location]
            if tile.terrain.biome == "water":
                # Oceans & lakes do not have ores
                continue
            base_production += tile.terrain.ores[ore]
        
        production = base_production * region.population

        return (ore, production)

    return mine_production

def steel_production(
        region: "Region",
        state: "GameState"
    ) -> tuple[str, float]:
    market = state.markets[region.market]
    iron_fill = get_fulfillment(market, "iron", state)
    coal_fill = get_fulfillment(market, "coal", state)
    limiter = min(iron_fill, coal_fill)
    production = limiter * region.population * steel_mult

    return ("steel", production)
    
def machinery_production(
        region: "Region",
        state: "GameState"
    ) -> tuple[str, float]:
    market = state.markets[region.market]
    iron_fill = get_fulfillment(market, "iron", state)
    copper_fill = get_fulfillment(market, "copper", state)
    limiter = min(iron_fill, copper_fill)
    production = limiter * region.population * machine_mult

    return ("machinery", production)

def luxuries_production(luxury: str) -> Callable[[str], tuple[str, float]]:
    """
    Creates a luxury production function for this industry based on the passed
    luxury type. All luxury industries just produce 1 unit in ideal conditions.
    """
    def luxury_production(
            region: "Region", 
            state: "GameState"
        ) -> tuple[str, float]:
        return (luxury, region.population * luxury_mult)
    
    return luxury_production

industry_types = {
    "subsistence": IndustryType(
        cost=0,
        production=subsistence_production,
        name="subsistence"
    ),
    "farming": IndustryType(
        cost=2,
        production=farming_production,
        name="farming"
    ),
    "iron_mining": IndustryType(
        cost=3,
        production=mines_production("iron"),
        name="iron_mining"
    ),
    "copper_mining": IndustryType(
        cost=3,
        production=mines_production("copper"),
        name="copper_mining"
    ),
    "gold_mining": IndustryType(
        cost=3,
        production=mines_production("gold"),
        name="gold_mining"
    ),
    "coal_mining": IndustryType(
        cost=3,
        production=mines_production("coal"),
        name="coal_mining"
    ),
    "oil_drilling": IndustryType(
        cost=4,
        production=mines_production("oil"),
        name="oil_drilling"
    ),
    "steelworks": IndustryType(
        cost=4,
        production=steel_production,
        name="steelworks"
    ),
    "foundry": IndustryType(
        cost=4,
        production=machinery_production,
        name="foundry"
    ),
    "textile": IndustryType(
        cost=3,
        production=luxuries_production("textiles"),
        name="textiles"
    ),
    "jewelry": IndustryType(
        cost=4,
        production=luxuries_production("jewelry"),
        name="jewelry"
    ),
    "spice": IndustryType(
        cost=4,
        production=luxuries_production("spice"),
        name="spice"
    ),
    "consumer_goods": IndustryType(
        cost=4,
        production=luxuries_production("consumer_goods"),
        name="consumer_goods"
    ),
    "horses": IndustryType(
        cost=4,
        production=luxuries_production("horses"),
        name="horses"
    ),
    "gems": IndustryType(
        cost=4,
        production=luxuries_production("gems"),
        name="gems"
    ),
    "glass": IndustryType(
        cost=4,
        production=luxuries_production("glass"),
        name="glass"
    )
}