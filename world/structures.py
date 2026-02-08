import logging
from typing import TYPE_CHECKING

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from world.map import Tile
    from game.resources import Resource

import scripts.database as db

from world.world import nation_list, tile_list, structures

class StructureType:
    """
    Contains data about a particular type of structure.
    """
    def __init__(self, usable_in: list, inf_cost: int, name: str, 
                 resource_cost: list[str] = [], prereq: str = '', 
                 tier_req: int = 0, resource_prod: str = ''):
        self.usable_in = usable_in
        self.inf_cost = inf_cost
        self.resource_cost = resource_cost
        self.name = name # Note that this is the capitalized and spaced version
        self.prereq = prereq # A structure that needs to be built first
        self.tier_req = tier_req # The city tier that the structure needs
        self.resource_prod = resource_prod # Resource produced when built

class LinkType:
    def __init__(self, oceanic: str, inf_cost: int, 
                 resource_cost: dict[str, int], tier: int, name: str):
        self.oceanic = oceanic
        self.inf_cost = inf_cost
        self.resource_cost = resource_cost
        self.tier = tier
        self.name = name

class Structure:
    def __init__(self, structure_type: StructureType | LinkType, 
                 location: tuple[int, int], root_city: str, builder: int):
        self.structure_type = structure_type
        self.location = location
        self.root_city = root_city # A link structure's root is the nearest of the two
        self.builder = builder # Nid of nation that built it

class City(Structure):
    def __init__(self, name: str, tier: int = 0, 
                 location: tuple[int, int] = (0, 0), owner: int = None, 
                 stability: int = 80, inventory: list["Resource"] = [], 
                 authority: str = None):
        super().__init__(structure_type=structure_types["city"], 
                         location=location, root_city=self, builder=owner)
        self.name = name
        self.tier = tier
        self.stability = stability
        self.inventory = inventory
        
        if authority == None:
            self.authority = nation_list[owner].name
        else:
            self.authority = authority

    async def save(self):
        await db.save_tile(tile_list[self.location])

    def find_resource(self, resource_name: str) -> "Resource":
        """
        Returns a resource in this city's inventory that is not currently consumed.
        If there's no matching resource, returns None.
        """
        for item in self.inventory:
            if (item.name == resource_name
                and item.used_in is None):
                return item
        
        # We weren't able to find a matching resource
        return None

    def raw_inventory(self) -> list[str]:
        return [item.name.split("_")[0] for item in self.inventory]

    def luxury_count(self) -> int:
        """
        Returns the number of unique luxuries in the city's inventory.
        """
        luxuries = []
        for item in self.inventory:
            if item.name.startswith("luxurygoods") and item not in luxuries:
                luxuries.append(item)
        return len(luxuries)

    def developed_area(self) -> list["Tile"]:
        """
        Returns all tiles in the city's developed area.
        """
        if self.tier == 4:
            return tile_list[self.location].metroarea()
        else:
            return tile_list[self.location].area()

    def structures(self) -> list[Structure]:
        """
        Returns a list of every structure whose root_city is this city.
        """
        city_structures = []
        for structure in structures:
            if structure.root_city == self.name:
                city_structures.append(structure)
        return city_structures

    def structure_types(self) -> list[StructureType]:
        """
        Returns a list of every structure type bound to this city without duplicates.
        """
        return list(set([structure.structure_type.name for structure in self.structures()]))

    def has_resource(self, resource: str) -> bool:
        """
        Returns true if this city has a resource with name 'resource.'
        """

    def calculate_tier(self) -> int:
        raw_inventory = self.raw_inventory()
        
        if "lumber" in raw_inventory and "food" in raw_inventory:
            if ("lumber" in raw_inventory 
                and "fuel" in raw_inventory 
                and raw_inventory.count("food") >= 2):
                if (raw_inventory.count("lumber") >= 2 
                    and raw_inventory.count("food") >= 3 
                    and raw_inventory.count("fuel") >= 2 
                    and self.luxury_count() >= 1):
                    if (raw_inventory.count("lumber") >= 3 
                        and raw_inventory.count("food") >= 5 
                        and raw_inventory.count("fuel") >= 3 
                        and self.luxury_count() >= 2):
                        return 4
                    return 3
                return 2
            return 1
        else:
            return 0

class Link:
    """
    A generalized class for infrastructure connections.
    
    :var linktype: A LinkType object.
    :var origin: The name of the city the link starts in. 
    :var destination: The name of the city the link ends in. Note that order doesn't matter, but may effect pathfinding.
    :var path: The list of locations which make up this link.
    :var owner: The userid of the nation which owns this link.
    """
    def __init__(self, linktype: LinkType, origin: City, destination: City, 
                 path: list[tuple[int, int]], owner: int, link_id = None):
        self.origin = origin
        self.destination = destination
        self.path = path
        self.owner = owner
        self.linktype = linktype
        self.link_id = link_id
    
    async def save(self):
        await db.save_link(self)

    def encode(self):
        """
        Returns a JSON-serializable tuple of info that can be used to identify this link at load.
        """
        return (self.origin.name, self.destination.name, self.owner)

structure_types = {
    # City structures
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
    "port": StructureType(
        usable_in=["city"], 
        inf_cost=2, 
        resource_cost=["stone", "lumber"], 
        name="Port"),
    "foundry": StructureType(
        usable_in=["city"], 
        inf_cost=2, 
        resource_cost=["metal", "fuel"], 
        name="Foundry",
        tier_req=2),

    # Resource Structures
    "aqueduct": StructureType(
        usable_in=["coastal"],
        inf_cost=1,
        name="Aqueduct"),
    "farm": StructureType(
        usable_in=["arable"],
        inf_cost=1,
        name="Farm",
        resource_prod="grain"),
    "orchard": StructureType(
        usable_in=["arable"],
        inf_cost=1,
        name="Orchard",
        resource_prod="fruit"),
    "pasture": StructureType(
        usable_in=["non-mountain"],
        inf_cost=1,
        name="Pasture",
        resource_prod="meat"),
    "fishery": StructureType(
        usable_in=["coastal"],
        inf_cost=1,
        name="Fishery",
        resource_prod="fish"),
    "forester": StructureType(
        usable_in=["arable"],
        inf_cost=1,
        name="Forester",
        resource_prod="wood"),
    "quarry": StructureType(
        usable_in=["mountain"],
        inf_cost=2,
        name="Quarry",
        resource_prod="stone"),
    "mine": StructureType(
        usable_in=["mountain"],
        inf_cost=2,
        name="Mine",
        resource_prod="fuel")
}

link_types = {
    "stone_road": LinkType(
        oceanic=False, 
        inf_cost=0.5, 
        resource_cost={"stone": 0.2, "metal": 0}, 
        name="Stone Road",
        tier=1),
    "simple_rail": LinkType(
        oceanic=False,
        inf_cost=1,
        resource_cost={"stone": 0, "metal": (1/3)},
        name="Simple Rail",
        tier=2),
    "quality_rail": LinkType(
        oceanic=False,
        inf_cost=2,
        resource_cost={"stone": 0, "metal": 0.5},
        name="Quality Rail",
        tier=3),
    "sea": LinkType(
        oceanic=True,
        inf_cost=0.2,
        resource_cost={"stone": 0, "metal": 0},
        name="Sea Route",
        tier=2)
}