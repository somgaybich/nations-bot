import logging
from typing import TYPE_CHECKING

from data.constants import update_season

if TYPE_CHECKING:
    from world.world import GameState

logger = logging.getLogger(__name__)

async def tick(state: "GameState"):
    """
    Processes a tick of the game system.
    """
    logger.info("Processing game tick...")
    
    # Resource distribution pass
    for market in state.markets.values():
        logger.debug(f"Processing distribution tick for {market.name}")
        # Do distribution stuff :P

    # Region pass
    for region in state.regions.values():
        logger.debug(f"Processing region tick for {region.name}")
        
        region.population += region.growth()
        
        region.city_tier = region.calculate_tier()
        await region.save()

    # Nation pass
    for nation in state.nations.values():
        logger.debug(f"Processing nation tick for {nation.name}")

        for unit_id in nation.units:
            unit = state.units[unit_id]
            # Any units that are currently in training graduate
            if unit.status == "TRAINING":
                unit.status = ""

        nation.econ.influence_cap = nation.econ.calculate_cap(state)
        nation.econ.influence = nation.econ.influence_cap
        
        await nation.save()
        await nation.econ.save()
        logger.debug(f"Tick for {nation.name} complete")

    update_season()
    logger.info("Game tick complete.")
