import logging

from world.world import nation_list
from game.constants import OVER_CAP_STABILITY_LOSS, update_season

logger = logging.getLogger(__name__)

async def tick():
    logger.info("Processing game tick...")
    for nation in nation_list.values():
        logger.debug(f"Processing tick for {nation.name}")
        for city in nation.cities.values():
            city.tier = city.calculate_tier()

            authority = nation.authorities[city.authority]
            cap_gap = authority.cap - len(authority.cities)
            if cap_gap < 0:
                city.stability += cap_gap * OVER_CAP_STABILITY_LOSS

            await city.save()

        nation.econ.influence_cap = nation.econ.calculate_cap()
        nation.econ.influence = nation.econ.influence_cap
        
        await nation.save()
        await nation.econ.save()
        logger.debug(f"Tick for {nation.name} complete")
    
    update_season()
    logger.info("Game tick complete.")
