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

class LinkType:
    def __init__(self, oceanic: str, inf_cost: int, 
                 resource_cost: dict[str, int], tier: int, fname: str, name: str):
        self.oceanic = oceanic
        self.inf_cost = inf_cost
        self.resource_cost = resource_cost
        self.tier = tier
        self.fname = fname
        self.name = name

class Structure:
    def __init__(self, structure_type: StructureType | LinkType, 
                 location: tuple[int, int], region: str, builder: int):
        self.structure_type = structure_type
        self.location = location
        self.region = region
        self.builder = builder # Nid of nation that built it

class Link:
    """
    A generalized class for infrastructure connections.
    
    :var linktype: A LinkType object.
    :var origin: The name of the city the link starts in. 
    :var destination: The name of the city the link ends in.
    :var path: The list of locations which make up this link.
    :var owner: The userid of the nation which owns this link.
    """
    def __init__(self, linktype: LinkType, origin: Structure, destination: Structure, 
                 path: list[tuple[int, int]], owner: int, 
                 transferred: int = 0, link_id = None):
        self.origin = origin
        self.destination = destination
        self.path = path
        self.owner = owner
        self.linktype = linktype
        self.transferred = transferred
        self.link_id = link_id
    
    async def save(self):
        await db.save_link(self)

    def encode(self):
        """
        Returns a JSON-serializable tuple of info that can be used to identify this link at load.
        """
        return (self.origin.name, self.destination.name, self.owner)

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

link_types = {
    "stone_road": LinkType(
        oceanic=False, 
        inf_cost=0.5, 
        resource_cost={"stone": 0.2, "metal": 0}, 
        fname="Stone Road",
        name="stone_road",
        tier=1),
    "simple_rail": LinkType(
        oceanic=False,
        inf_cost=1,
        resource_cost={"stone": 0, "metal": (1/3)},
        fname="Simple Rail",
        name="simple_rail",
        tier=2),
    "quality_rail": LinkType(
        oceanic=False,
        inf_cost=2,
        resource_cost={"stone": 0, "metal": 0.5},
        fname="Quality Rail",
        name="quality_rail",
        tier=3),
    "sea": LinkType(
        oceanic=True,
        inf_cost=0.2,
        resource_cost={"stone": 0, "metal": 0},
        fname="Sea Route",
        name="sea",
        tier=2)
}