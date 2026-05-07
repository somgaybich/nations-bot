import logging

logger = logging.getLogger(__name__)

import scripts.database as db

from world.world import nation_list

class Econ:
    """
    Represents a nation's economy.
    """
    nationid: int
    """
    The NID of the parent nation.
    """
    influence: int
    """
    The influence currently available.
    """
    influence_cap: int
    """
    The maximum influence usable per season.
    """

    def __init__(self, nationid: int, influence: int = 2, 
                 influence_cap: int = 2):
        """
        :param nationid: The NID of the parent nation.
        :param influence: The influence currently available.
        :param influence_cap: The maximum influence usable per season.
        :type nationid: int
        :type influence: int
        :type influence_cap: int
        """
        self.nationid = nationid
        self.influence = influence
        self.influence_cap = influence_cap

    async def save(self):
        """
        Saves this economy to the database.
        """
        await db.save_economy(self)
    
    def calculate_cap(self) -> int:
        """
        Calculates a new influence cap for this economy. Does not actually
        assign or save the new cap value.
        """
        cap = 1
        nation = nation_list[self.nationid]
        for city in nation.regions.values():
            cap = city.city_tier + 1
            
            if "District" in city.structure_types():
                cap += 2
            
            luxuries = len(city.inventory)
            if city.city_tier == 3:
                luxuries -= 1
            elif city.city_tier == 4:
                luxuries -= 2
            cap += luxuries
        
        # TODO: Consider infrastructure quality?

        return cap