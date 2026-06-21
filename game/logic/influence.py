from typing import TYPE_CHECKING
import logging

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from world.world import GameState
    from game.objs.economy import Econ

def calculate_cap(economy: "Econ", state: "GameState") -> int:
    """
    Calculates a new influence cap for an economy.
    """
    cap = 1
    nation = state.nations[economy.nationid]
    for region_id in nation.regions:
        region = state.regions[region_id]
        cap += region.city_tier + 1

    return cap