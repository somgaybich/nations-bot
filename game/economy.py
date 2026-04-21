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
            
            cap += city.tier + 1
            if authority.authtype == "oligarchic":
                cap += 1
            if "District" in city.structure_types():
                cap += 2
                if authority.authtype == "oligarchic":
                    cap += 1
            
            luxuries = city.luxury_count()
            if city.tier == 3:
                luxuries -= 1
            elif city.tier == 4:
                luxuries -= 2
            cap += luxuries
        
        for link in nation.links:
            # This code was broken in the region rework, fix in the link rework
            if link.origin in nation.regions:
                dest_authority = nation.authorities[link.origin.authority]
                if (dest_authority.authtype == "industrial"):
                    cap += 1
            elif link.destination in nation.regions:
                dest_authority = nation.authorities[link.destination.authority]
                if (dest_authority.authtype == "industrial"):
                    cap += 1
                    
            match link.linktype.fname:
                case "Stone Road":
                    cap += 1

                case "Simple Rail":
                    if "Central Station" in link.origin.structure_types():
                        cap += 2
                    elif "Station" in link.origin.structure_types():
                        cap += 1

                    if "Central Station" in link.destination.structure_types():
                        cap += 2
                    elif "Station" in link.destination.structure_types():
                        cap += 1

                    cap += 3

                case "Simple Rail":
                    if "Central Station" in link.origin.structure_types():
                        cap += 2
                    elif "Station" in link.origin.structure_types():
                        cap += 1

                    if "Central Station" in link.destination.structure_types():
                        cap += 2
                    elif "Station" in link.destination.structure_types():
                        cap += 1

                    cap += 5

                case "Sea Route":
                    if ("Port" in link.origin.structure_types() 
                        and "Port" in link.destination.structure_types()):
                        cap += 4
                    elif ("Port" in link.origin.structure_types() 
                        or "Port" in link.destination.structure_types()):
                        cap += 2
                    
                    cap += 3

        return cap