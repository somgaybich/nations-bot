import logging

from world.world import nation_list
from game.constants import authority_settings, update_season

logger = logging.getLogger(__name__)

async def tick():
    logger.info("Processing game tick...")
    for nation in nation_list.values():
        logger.debug(f"Processing tick for {nation.name}")
        for region in nation.regions.values():
            region.tier = region.calculate_tier()

            authority = nation.authorities[region.authority]
            cap_gap = authority.cap - len(authority.cities)
            if cap_gap < 0:
                region.stability += cap_gap * authority_settings["over_cap_stability_loss"]
            match authority.authtype:
                case "oligarchic":
                    stability_change = authority_settings["auth_stability_decay"] * (authority_settings["max_auth_stability_loss"] - (region.tier * authority_settings["oligarchy_stability_loss_factor"]))
                case "militaristic":
                    stability_change = authority_settings["auth_stability_decay"] * authority_settings["max_auth_stability_loss"]
            region.stability -= stability_change

            await region.save()

        nation.econ.influence_cap = nation.econ.calculate_cap()
        nation.econ.influence = nation.econ.influence_cap
        
        await nation.save()
        await nation.econ.save()
        logger.debug(f"Tick for {nation.name} complete")
    
    update_season()
    logger.info("Game tick complete.")
