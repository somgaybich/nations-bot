import logging
from typing import TYPE_CHECKING

from game.data.constants import (update_season, stability_loss_factor, 
                                 satisfaction_loss_exponent, 
                                 satisfaction_gain_exponent,
                                 stability_gain_factor)

from game.logic.influence import calculate_cap
from game.logic.growth import growth, calculate_tier, region_satisfaction

if TYPE_CHECKING:
    from world.world import GameState
    from game.objs.region import Region

logger = logging.getLogger(__name__)

def reduce_stability(region: "Region", satisfaction: float):
    satisfaction_deficit = 1 - (satisfaction ** satisfaction_loss_exponent)
    region.stability -= satisfaction_deficit * stability_loss_factor

def increase_stability(region: "Region", satisfaction: float):
    true_satisfaction = satisfaction ** satisfaction_gain_exponent
    region.stability += true_satisfaction * stability_gain_factor

async def tick(state: "GameState"):
    """
    Processes a tick of the game system.
    """
    logger.info("Processing game tick...")

    # Region pass
    for region in state.regions.values():
        logger.debug(f"Processing region tick for {region.name}")
        
        region.population += growth(region)
        
        satisfaction = region_satisfaction(region, state)
        if satisfaction < 0.8:
            reduce_stability(region, satisfaction)

        region.city_tier = calculate_tier(region)
        await region.save()

    # Nation pass
    for nation in state.nations.values():
        logger.debug(f"Processing nation tick for {nation.name}")

        for unit_id in nation.units:
            unit = state.units[unit_id]
            # Any units that are currently in training graduate
            if unit.status == "TRAINING":
                unit.status = ""

        nation.econ.influence_cap = calculate_cap(nation.econ, state)
        nation.econ.influence = nation.econ.influence_cap
        
        await nation.save()
        await nation.econ.save()
        logger.debug(f"Tick for {nation.name} complete")

    update_season()
    logger.info("Game tick complete.")
