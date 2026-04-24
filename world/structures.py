import logging

logger = logging.getLogger(__name__)

import scripts.database as db

class StructureType:
    """
    Contains data about a particular type of structure.
    """
    def __init__(self, usable_in: list, inf_cost: int, fname: str, name: str,
                 resource_cost: list[str] = [], prereq: str = '', 
                 tier_req: int = 0, resource_prod: str = ''):
        self.usable_in = usable_in # Negative, leave empty for no requirements
        self.inf_cost = inf_cost
        self.resource_cost = resource_cost
        self.fname = fname # Note that this is the capitalized and spaced version
        self.name = name
        self.prereq = prereq # A structure that needs to be built first
        self.tier_req = tier_req # The city tier that the structure needs
        self.resource_prod = resource_prod # Resource produced when built

class Structure:
    def __init__(self, structure_type: StructureType, 
                 location: tuple[int, int], region: str, builder: int):
        self.structure_type = structure_type
        self.location = location
        self.region = region
        self.builder = builder # Nid of nation that built it

structure_types = {
    # Dummy types
    # Note these aren't ever passed through anything and are only used
    # when looking up structures for maps
    # (This is kind of a silly workaround but works fine)
    "outpost": StructureType(
        usable_in=[],
        inf_cost=0,
        fname="Outpost",
        name="outpost"),
    "village": StructureType(
        usable_in=[],
        inf_cost=0,
        fname="Village",
        name="village"),
    "town": StructureType(
        usable_in=[],
        inf_cost=0,
        fname="Town",
        name="town"),
    "city": StructureType(
        usable_in=[],
        inf_cost=0,
        fname="City",
        name="city"),
    "metropolis": StructureType(
        usable_in=[],
        inf_cost=0,
        fname="Metropolis",
        name="metropolis"),

    # City structures
    "temple": StructureType(
        usable_in=["city"], 
        inf_cost=1, 
        resource_cost=["stone"], 
        fname="Temple",
        name="temple"),
    "grandtemple": StructureType(
        usable_in=["city"], 
        inf_cost=1, 
        resource_cost=["stone"], 
        fname="Grand Temple", 
        name="grandtemple",
        prereq="Temple"),
    "station": StructureType(
        usable_in=["city"], 
        inf_cost=2, 
        resource_cost=["lumber"], 
        fname="Station",
        name="station"),
    "centralstation": StructureType(
        usable_in=["city"], 
        inf_cost=2, 
        resource_cost=["lumber"], 
        fname="Central Station", 
        name="centralstation",
        prereq="Station"),
    "district": StructureType(
        usable_in=["city"], 
        inf_cost=1, 
        resource_cost=["lumber", "stone"], 
        fname="District",
        name="district"),
    "charcoalpit": StructureType(
        usable_in=["city"], 
        inf_cost=2, 
        resource_cost=["lumber"], 
        fname="Charcoal Pit",
        name="charcoalpit"),
    "smeltery": StructureType(
        usable_in=["city"], 
        inf_cost=2, 
        resource_cost=["stone", "fuel"], 
        fname="Smeltery",
        name="smeltery"),
    "port": StructureType(
        usable_in=["city"], 
        inf_cost=2, 
        resource_cost=["stone", "lumber"], 
        fname="Port",
        name="port"),
    "foundry": StructureType(
        usable_in=["city"], 
        inf_cost=2, 
        resource_cost=["metal", "fuel"], 
        fname="Foundry",
        name="foundry",
        tier_req=2),

    # Resource Structures
    "aqueduct": StructureType(
        usable_in=["coastal"],
        inf_cost=1,
        fname="Aqueduct",
        name="aqueduct"),
    "farm": StructureType(
        usable_in=["arable"],
        inf_cost=1,
        fname="Farm",
        name="farm",
        resource_prod="grain"),
    "orchard": StructureType(
        usable_in=["arable"],
        inf_cost=1,
        fname="Orchard",
        name="orchard",
        resource_prod="fruit"),
    "pasture": StructureType(
        usable_in=["non-mountain"],
        inf_cost=1,
        fname="Pasture",
        name="pasture",
        resource_prod="meat"),
    "fishery": StructureType(
        usable_in=["coastal"],
        inf_cost=1,
        fname="Fishery",
        name="fishery",
        resource_prod="fish"),
    "forester": StructureType(
        usable_in=["arable"],
        inf_cost=1,
        fname="Forester",
        name="forester",
        resource_prod="wood"),
    "quarry": StructureType(
        usable_in=["mountain"],
        inf_cost=2,
        fname="Quarry",
        name="quarry",
        resource_prod="stone"),
    "mine": StructureType(
        usable_in=["mountain"],
        inf_cost=2,
        fname="Mine",
        name="mine",
        resource_prod="fuel")
}