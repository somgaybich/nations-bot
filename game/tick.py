import logging

from world.world import nation_list
from game.constants import update_season

logger = logging.getLogger(__name__)

async def tick():
    """
    Processes a tick of the game system.
    """
    logger.info("Processing game tick...")
    for nation in nation_list.values():
        logger.debug(f"Processing tick for {nation.name}")
        # Logistics pass
        for market in nation.markets.values():
            for region in market.regions:
                # Passive food production
                market.surplus["food"] += region.arability()

                region.city_tier = region.calculate_tier()
                await region.save()

        for unit in nation.military.values():
            # Any units that are currently in training graduate
            if unit.status == "TRAINING":
                unit.status = ""

        nation.econ.influence_cap = nation.econ.calculate_cap()
        nation.econ.influence = nation.econ.influence_cap
        
        await nation.save()
        await nation.econ.save()
        logger.debug(f"Tick for {nation.name} complete")
    
    update_season()
    logger.info("Game tick complete.")
