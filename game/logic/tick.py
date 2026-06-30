import logging
from typing import TYPE_CHECKING

from game.data.constants import update_season

from game.logic.influence import calculate_cap
from game.logic.growth import growth, calculate_tier

if TYPE_CHECKING:
    from world.world import GameState

logger = logging.getLogger(__name__)

async def tick(state: "GameState"):
    """
    Processes a tick of the game system.
    """
    logger.info("Processing game tick...")

    # Region pass
    for region in state.regions.values():
        logger.debug(f"Processing region tick for {region.name}")
        
        region.population += growth(region)
        
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
