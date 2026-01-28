import logging

logger = logging.getLogger(__name__)

import scripts.database as db

from world.structures import link_types
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
            if city.structures.has("District"):
                cap += 2
            
            luxuries = city.luxury_count()
            if city.tier == 3:
                luxuries -= 1
            elif city.tier == 4:
                luxuries -= 2
            cap += luxuries
        
        for link in nation.links:
            match link.linktype.name:
                case "Stone Road":
                    cap += 1
                    
                case "Simple Rail":
                    if link.origin.structures.has("Central Station"):
                        cap += 2
                    elif link.origin.structures.has("Station"):
                        cap += 1

                    if link.destination.structures.has("Central Station"):
                        cap += 2
                    elif link.destination.structures.has("Station"):
                        cap += 1

                    cap += 3

                case "Quality Rail":
                    if link.origin.structures.has("Central Station"):
                        cap += 2
                    elif link.origin.structures.has("Station"):
                        cap += 1

                    if link.destination.structures.has("Central Station"):
                        cap += 2
                    elif link.destination.structures.has("Station"):
                        cap += 1

                    cap += 5

                case "Sea Route":
                    if link.origin.structures.has("Port") and link.destination.structures.has("Port"):
                        cap += 4
                    elif link.origin.structures.has("Port") or link.origin.structures.has("Port"):
                        cap += 2
                    
                    cap += 3
            
            structures = nation.cities[link.origin].structures + nation.cities[link.destination].structures
            for structure in structures:
                if structure == "station" and link.linktype == "simple_rail" or link.linktype == "quality_rail":
                    cap += 1
                if structure == "port" and link.linktype == "sea":
                    cap += 2

        return 1