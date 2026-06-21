from typing import TYPE_CHECKING

from game.data.constants import (food_shortage_contract_rate, 
                                 food_surplus_use_rate)
from game.logic.logistics import get_supply

if TYPE_CHECKING:
    from game.objs.region import Region
    from world.world import GameState

def growth(region: "Region", state: "GameState"):
    """
    Returns the amount the population of the target region will grow according
    to the current supplies in the market.
    """
    market = state.markets[region.market]
    regions = len(market.regions)
    available_food = get_supply(market, "food", state)
    # We'll use some % of our surplus
    growth_rate = available_food / regions * food_surplus_use_rate
    if growth_rate < 0:
        # If we have a shortage, we should shrink slower
        growth_rate *= food_shortage_contract_rate
    
    # FIXME: Incorporate other resources based on tier

    return growth_rate

def calculate_tier(region: "Region") -> int:
    """
    Recalculates the tier of the target region's core city.
    """ 
    #FIXME
    pass