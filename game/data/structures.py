import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
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