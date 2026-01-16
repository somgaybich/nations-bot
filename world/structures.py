import logging
from typing import TYPE_CHECKING

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from world.cities import City

import scripts.database as db

class StructureType:
    """
    Contains data about a particular type of structure.
    """
    def __init__(self, usable_in: list, inf_cost: int, resource_cost: list[str], name: str, prereq: str = '', tier_req: int = 0):
        self.usable_in = usable_in
        self.inf_cost = inf_cost
        self.resource_cost = resource_cost
        self.name = name
        self.prereq = prereq # An structure that needs to be built first
        self.tier_req = tier_req # The city tier that the structure needs to be built in

class LinkType:
    def __init__(self, oceanic: str, inf_cost: int, resource_cost: dict[str, int], name: str):
        self.oceanic = oceanic
        self.inf_cost = inf_cost
        self.resource_cost = resource_cost
        self.name = name

class Link:
    """
    A generalized class for infrastructure connections.
    
    :var linktype: A LinkType object.
    :var origin: The name of the city the link starts in. 
    :var destination: The name of the city the link ends in. Note that order doesn't matter, but may effect pathfinding.
    :var path: The list of locations which make up this link.
    :var owner: The userid of the nation which owns this link.
    """
    def __init__(self, linktype: LinkType, origin: "City", destination: "City", path: list[tuple[int, int]], owner: int, link_id = None):
        self.origin = origin
        self.destination = destination
        self.path = path
        self.owner = owner
        self.linktype = linktype
        self.link_id = link_id
    
    async def save(self):
        await db.save_link(self)

class Structure:
    def __init__(self, structure_type: StructureType | LinkType, location: tuple[int, int], root_city: str, builder: int):
        self.structure_type = structure_type
        self.location = location
        self.root_city = root_city # A link structure's root is the nearest of the two
        self.builder = builder # Nid of nation that built it

class StructureList(list[Structure]):
    def __init__(self):
        super().__init__()
    
    def has(self, name: str) -> bool:
        """
        Checks if a structurelist contains a structure type
        """
        for structure in self:
            if structure.structure_type.name == name:
                return True
        return False

structure_types = {
    "temple": StructureType(
        usable_in=["city"], 
        inf_cost=1, 
        resource_cost=["stone"], 
        name="Temple"),
    "grandtemple": StructureType(
        usable_in=["city"], 
        inf_cost=1, 
        resource_cost=["stone"], 
        name="Grand Temple", 
        prereq="Temple"),
    "station": StructureType(
        usable_in=["city"], 
        inf_cost=2, 
        resource_cost=["lumber"], 
        name="Station"),
    "centralstation": StructureType(
        usable_in=["city"], 
        inf_cost=2, 
        resource_cost=["lumber"], 
        name="Central Station", 
        prereq="Station"),
    "district": StructureType(
        usable_in=["city"], 
        inf_cost=1, 
        resource_cost=["lumber", "stone"], 
        name="District"),
    "charcoalpit": StructureType(
        usable_in=["city"], 
        inf_cost=2, 
        resource_cost=["lumber"], 
        name="Charcoal Pit"),
    "smeltery": StructureType(
        usable_in=["city"], 
        inf_cost=2, 
        resource_cost=["stone", "fuel"], 
        name="Smeltery"),
    "port": StructureType(usable_in=["city"], 
        inf_cost=2, 
        resource_cost=["stone", "lumber"], 
        name="Port"),
    "foundry": StructureType(
        usable_in=["city"], 
        inf_cost=2, 
        resource_cost=["metal", "fuel"], 
        name="Foundry", tier_req=2),
}

link_types = {
    "stone_road": LinkType(
        oceanic=False, 
        inf_cost=0.5, 
        resource_cost={"stone": 0.2, "metal": 0}, 
        name="Stone Road"),
    "simple_rail": LinkType(
        oceanic=False,
        inf_cost=1,
        resource_cost={"stone": 0, "metal": (1/3)},
        name="Simple Rail"),
    "quality_rail": LinkType(
        oceanic=False,
        inf_cost=2,
        resource_cost={"stone": 0, "metal": 0.5},
        name="Quality Rail"),
    "sea": LinkType(
        oceanic=True,
        inf_cost=0.2,
        resource_cost={"stone": 0, "metal": 0},
        name="Sea Route")
}