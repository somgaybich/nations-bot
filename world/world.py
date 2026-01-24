from typing import TYPE_CHECKING
import logging

logger = logging.getLogger(__name__)

import scripts.errors as errors

if TYPE_CHECKING:
    from game.military import Unit
    from world.map import Tile
    from game.nation import Nation

class TileDict(dict[tuple[int, int], "Tile"]):
    """
    A singleton class for storing tile data.
    """

class NationDict(dict[int, "Nation"]):
    """
    A singleton for storing nation data.
    """
    def __getitem__(self, key: int) -> "Nation":
        if key not in self.keys():
            raise errors.NationIDNotFound(key)
        else:
            return super().__getitem__(key)

tile_list: TileDict = TileDict()
units: list["Unit"] = []
nation_list: NationDict = NationDict()