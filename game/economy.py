import logging

logger = logging.getLogger(__name__)

import scripts.database as db

from world.world import nation_list

class Econ:
    """
    Represents a nation's economy.
    """
    def __init__(self, nationid: int, influence: int = 2, influence_cap: int = 2):
        self.nationid = nationid
        self.influence = influence
        self.influence_cap = influence_cap

    async def save(self):
        await db.save_economy(self)
    
    def calculate_cap(self) -> int:
        cap = 1
        nation = nation_list[self.nationid]
        for city in nation.cities.values():
            cap += city.tier + 1
            if "district" in city.structures:
                cap += 2
            
            luxuries = city.luxury_count()
            if city.tier == 3:
                luxuries -= 1
            elif city.tier == 4:
                luxuries -= 2
            cap += luxuries
        
        for link in nation.links:
            match link.linktype:
                case "stone":
                    cap += 1
                case "sea":
                    cap += 1
                case "simple_rail":
                    cap += 3
                case "quality_rail":
                    cap += 5
            
            structures = nation.cities[link.origin].structures + nation.cities[link.destination].structures
            for structure in structures:
                if structure == "station" and link.linktype == "simple_rail" or link.linktype == "quality_rail":
                    cap += 1
                if structure == "port" and link.linktype == "sea":
                    cap += 2

        return 1