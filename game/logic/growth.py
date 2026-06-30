from typing import TYPE_CHECKING
import logging
import random

from game.data.constants import (contract_rate, 
                                 surplus_use_rate, no_luxury_weight,
                                 luxury_env_bonus, luxury_industries)
from game.data.luxuries import luxury_types
from game.logic.logistics import get_supply

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

def growth(region: "Region", state: "GameState"):
    """
    Returns the amount the population of the target region will grow according
    to the current supplies in the market.
    """
    market = state.markets[region.market]
    regions = len(market.regions)
    available_food = get_supply(market, "food", state)
    # We'll use some % of our surplus
    food_growth_rate = available_food / regions * surplus_use_rate
    if food_growth_rate < 0:
        # If we have a shortage, we should shrink slower
        return food_growth_rate * contract_rate

    if region.city_tier < 1:
        return food_growth_rate

    available_steel = get_supply(market, "steel", state)
    steel_growth_rate = available_steel / regions * surplus_use_rate
    if steel_growth_rate < 0:
        return steel_growth_rate * contract_rate
    
    if region.city_tier < 2:
        return min(food_growth_rate, steel_growth_rate)

    available_coal = get_supply(market, "coal", state)
    available_oil = get_supply(market, "oil", state)
    available_energy = available_coal + available_oil
    energy_growth_rate = available_energy / regions * surplus_use_rate
    if energy_growth_rate < 0:
        return energy_growth_rate * contract_rate
    
    true_growth_rate = min(
        food_growth_rate, energy_growth_rate, steel_growth_rate
    )
    if region.city_tier < 3:
        return true_growth_rate

    luxury_count = 0
    for luxury in luxury_industries:
        if get_supply(market, luxury, state) <= 0:
            continue
        luxury_count += 1
    
    if luxury_count <= region.city_tier - 3:
        # There's not enough variety of luxuries for this region to grow
        return 0
    
    return true_growth_rate

def calculate_tier(region: "Region") -> int:
    """
    Recalculates the tier of the target region's core city.
    """ 
    #FIXME
    return 0