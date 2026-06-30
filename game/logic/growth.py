from typing import TYPE_CHECKING
import logging
import random

from game.data.constants import (contract_rate, 
                                 surplus_use_rate, no_luxury_weight,
                                 luxury_env_bonus, luxury_industries)
from game.data.luxuries import luxury_types
from game.logic.logistics import get_supply, get_fulfillment

if TYPE_CHECKING:
    from game.objs.region import Region
    from world.world import GameState

logger = logging.getLogger(__name__)

def roll_luxuries(region: "Region", state: "GameState") -> str | None:
    """
    Roll to generate a new rare luxury in a region. Should only be called once
    when the region is first created. Returns the name of the luxury if one
    spawns, otherwise None.
    """
    luxuries = {}
    for luxury in luxury_types:
        weight = 1
        for location in region.tiles:
            tile = state.tiles[location]
            biome = tile.terrain.biome
            if biome in luxury.envs.keys():
                weight += luxury_env_bonus * luxury.envs[biome]
        
        luxuries[luxury.resource] = weight
    
    luxuries[None] = no_luxury_weight
    logger.debug(f"Luxury weights for {region.name}: {luxuries}")
    keys=list(luxuries.keys())
    vals=list(luxuries.values())
    choice = random.choices(keys, weights=vals)
    logger.debug(f"Chose {choice}")

    return choice

def luxury_count(region: "Region", state: "GameState"):
    market = state.markets[region.market]
    count = 0
    for luxury in luxury_industries:
        if get_supply(market, luxury, state) <= 0:
            continue
        count += 1
    return count

def region_satisfaction(region: "Region", state: "GameState"):
    """
    Returns a float value of how well supplied the region is.
    """
    satisfaction = 1

    satisfaction *= get_fulfillment(region.market, "food", state)
    if region.city_tier < 1:
        return satisfaction
    
    satisfaction *= get_fulfillment(region.market, "steel", state)
    if region.city_tier < 2:
        return satisfaction
    
    coal_ful = get_fulfillment(region.market, "coal", state)
    oil_ful = get_fulfillment(region.market, "oil", state)
    satisfaction *= max(coal_ful, oil_ful)

    if region.city_tier < 3:
        return satisfaction
    
    luxury_variety = luxury_count(region, state)
    satisfaction *= (region.city_tier - 3) / luxury_variety

def growth_rate(available, regions):
    """
    A helper function for growth() that calculates a rate and whether to finish
    checking resources.
    """
    rate = available / regions * surplus_use_rate

    if rate < 0:
        return rate * contract_rate, True
    return rate, True

def growth(region: "Region", state: "GameState"):
    """
    Returns the amount the population of the target region will grow according
    to the current supplies in the market.
    """
    market = state.markets[region.market]
    regions = market.regions
    # We'll use some % of our surplus
    food_growth_rate, done = growth_rate(
        available=get_supply(market, "food", state), 
        regions=regions
    )
    if region.city_tier < 1 or done:
        return food_growth_rate

    steel_growth_rate, done = growth_rate(
        available=get_supply(market, "steel", state),
        regions=regions
    )
    if region.city_tier < 2 or done:
        return min(food_growth_rate, steel_growth_rate)

    energy_growth_rate, done = growth_rate(
        available=get_supply(market, "coal", state) 
                  + get_supply(market, "oil", state),
        regions=regions
    )
    
    true_growth_rate = min(
        food_growth_rate, energy_growth_rate, steel_growth_rate
    )
    if region.city_tier < 3 or done:
        return true_growth_rate

    luxury_variety = luxury_count(region, state)
    if luxury_variety <= region.city_tier - 3:
        # There's not enough variety of luxuries for this region to grow
        return 0
    
    return true_growth_rate

def calculate_tier(region: "Region") -> int:
    """
    Recalculates the tier of the target region's core city.
    """ 
    #FIXME
    return 0