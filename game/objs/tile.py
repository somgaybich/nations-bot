import logging
from typing import TYPE_CHECKING
from dataclasses import dataclass

logger = logging.getLogger(__name__)

import world.database as db

if TYPE_CHECKING:
    from game.objs.structure import Structure
    from game.objs.terrain import Terrain

@dataclass
class Tile:
    """
    A tile on the game map.
    """
    terrain: "Terrain"
    """
    A terrain object that corresponds to this tile's physical conditions.
    """
    location: tuple[int, int]
    """
    The (q, r) axial coordinates of this tile on the game map.
    """
    owner: int | None = None
    """
    The id of the region that owns this tile, if any.
    """
    structure: "Structure | None" = None
    """
    The player-built structure object on this tile.
    """

    async def save(self):
        """
        Saves this tile to the database.
        """
        await db.save_tile(self)