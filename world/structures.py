import logging

logger = logging.getLogger(__name__)

class StructureType:
    """
    A specific type of structure. Encodes the requirements and behavior
    of a structure in the game. These should not be created dynamically,
    only on system startup.
    """
    usable_in: list[str]
    """
    A list of the environments required for this structure to be built.
    Currently implemented: arable, coastal, non-mountain, mountain, city
    """
    inf_cost: int
    """
    The amount of influence the builder nation will lose for building this
    structure.
    """
    fname: str
    """
    The name that will be displayed to the user.
    """
    name: str
    """
    The internal name for this structure type.
    """
    resource_cost: list[str]
    """
    The resource types needed to build this structure.
    """
    prereq: str
    """
    The internal name of the structure that needs to be built before this one.
    """
    tier_req: int
    """
    The minimum city tier this structure can be built at.
    """
    resource_prod: str
    """
    The resource, if any, that this structure produces.
    """

    def __init__(self, usable_in: list, inf_cost: int, fname: str, name: str,
                 resource_cost: list[str] = [], prereq: str = '', 
                 tier_req: int = 0, resource_prod: str = ''):
        """
        :param usable_in: A list of the environments required for this 
            structure to be built. Currently implemented: arable, coastal, 
            non-mountain, mountain, city
        :param inf_cost: The amount of influence the builder nation will lose 
            for building this structure.
        :param fname: The name that will be displayed to the user.
        :param name: The internal name for this structure type.
        :param resource_cost: The resource types needed to build this 
            structure.
        :param prereq: The internal name of the structure that needs to be 
            built before this one.
        :param tier_req: The minimum city tier this structure can be built at.
        :param resource_prod: The resource, if any, that this structure 
            produces.
        :type usable_in: list[str]
        :type inf_cost: int
        :type fname: str
        :type name: str
        :type resource_cost: list[str]
        :type prereq: str
        :type tier_req: int
        :type resource_prod: str
        """
        self.usable_in = usable_in
        self.inf_cost = inf_cost
        self.resource_cost = resource_cost
        self.fname = fname
        self.name = name
        self.prereq = prereq
        self.tier_req = tier_req
        self.resource_prod = resource_prod

class Structure:
    """
    A player-built structure on the map.
    """
    structure_type: StructureType
    """
    The type of structure that this is. Encodes the costs and behaviors of this
    structure.
    """
    location: tuple[int, int]
    """
    The location of the tile where this structure is built.
    """
    region: str
    """
    The name of the region this structure belongs to.
    """
    owner: int
    """
    The NID of the nation that this structure belongs to.
    """
    def __init__(self, structure_type: StructureType, 
                 location: tuple[int, int], region: str, owner: int):
        """
        :param structure_type: The type of structure that this is. Encodes the 
            costs and behaviors of this structure.
        :param location: The location of the tile where this structure is 
            built.
        :param region: The name of the region this structure belongs to.
        :param owner: The NID of the nation that this structure belongs to.
        :type structure_type: StructureType
        :type location: tuple[int, int]
        :type region: str
        :type owner: int
        """
        self.structure_type = structure_type
        self.location = location
        self.region = region
        self.owner = owner

structure_types = {
    # Dummy types
    # Only used for rendering
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