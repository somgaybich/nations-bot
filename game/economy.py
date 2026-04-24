import logging

logger = logging.getLogger(__name__)

import scripts.database as db

from world.world import nation_list

class Econ:
    """
    Represents a nation's economy.
    """
    def __init__(self, nationid: int, influence: int = 2, 
                 influence_cap: int = 2):
        self.nationid = nationid
        self.influence = influence
        self.influence_cap = influence_cap

    async def save(self):
        await db.save_economy(self)
    
    def calculate_cap(self) -> int:
        cap = 1
        nation = nation_list[self.nationid]
        for city in nation.regions.values():
            authority = nation.authorities[city.authority]
            
            cap += city.city_tier + 1
            if authority.authtype == "oligarchic":
                cap += 1
            if "District" in city.structure_types():
                cap += 2
                if authority.authtype == "oligarchic":
                    cap += 1
            
            luxuries = city.luxury_count()
            if city.city_tier == 3:
                luxuries -= 1
            elif city.city_tier == 4:
                luxuries -= 2
            cap += luxuries
        
        # TODO: Consider infrastructure quality?

        return cap