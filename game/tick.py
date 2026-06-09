import logging

from game.constants import update_season

from world.world import nation_list, markets, regions

logger = logging.getLogger(__name__)

async def tick():
    """
    Processes a tick of the game system.
    """
    logger.info("Processing game tick...")
    
    # Resource distribution pass
    for market in markets.values():
        logger.debug(f"Processing distribution tick for {market.name}")
        # Do distribution stuff :P

    # Region pass
    for region in regions.values():
        logger.debug(f"Processing region tick for {region.name}")
        
        region.population += region.growth()
        
        region.city_tier = region.calculate_tier()
        await region.save()

    # Nation pass
    for nation in nation_list.values():
        logger.debug(f"Processing nation tick for {nation.name}")

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
