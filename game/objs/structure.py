from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from data.structures import StructureType

@dataclass
class Structure:
    """
    A player-built structure on the map.
    """
    structure_type: "StructureType"
    """
    The type of structure that this is. Encodes the costs and behaviors of this
    structure.
    """
    location: tuple[int, int]
    """
    The location of the tile where this structure is built.
    """
    region: int
    """
    The ID of the region that owns this structure.
    """
    owner: int
    """
    The NID of the nation that this structure belongs to.
    """