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

    def __init__(self, usable_in: list, inf_cost: int, fname: str, name: str):
        """
        :param usable_in: A list of the environments required for this 
            structure to be built. Currently implemented: arable, coastal, 
            non-mountain, mountain, city
        :param inf_cost: The amount of influence the builder nation will lose 
            for building this structure.
        :param fname: The name that will be displayed to the user.
        :param name: The internal name for this structure type.
        :type usable_in: list[str]
        :type inf_cost: int
        :type fname: str
        :type name: str
        """
        self.usable_in = usable_in
        self.inf_cost = inf_cost
        self.fname = fname
        self.name = name

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

    # Here's where I would put my military structures definitions... if I had any
    # Sad trombone sound
}