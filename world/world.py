from typing import TYPE_CHECKING
import logging

logger = logging.getLogger(__name__)

import scripts.errors as errors

if TYPE_CHECKING:
    from game.military import Unit
    from world.map import Tile
    from world.nation import Nation

class TileDict(dict[tuple[int, int], "Tile"]):
    """
    A singleton class for storing tile data.
    """

    def _check_bounds(self, key: tuple[int, int]) -> None:
        try:
            x, y = key
        except (TypeError, ValueError):
            raise TypeError("Must access the tile list with a tuple of two ints")
        
        if not (-64 <= x and x <= 65 and -72 <= y and y <= 72):
            raise errors.TileOutOfBounds(key)

    def __getitem__(self, key: tuple[int, int]) -> "Tile":
        self._check_bounds(key)
        try:
            return super().__getitem__(key)
        except Exception as e:
            logger.warning(f"Failed to getitem tile at {key}: {e}")
    
    def __setitem__(self, key: tuple[int, int], value: "Tile") -> None:
        self._check_bounds(key)
        try:
            super().__setitem__(key, value)
        except Exception as e:
            logger.warning(f"Failed to set tile at {key}: {e}")
    
    def get(self, key, default=None):
        self._check_bounds(key)
        try:
            return super().get(key, default)
        except Exception as e:
            logger.warning(f"Failed to get tile at {key}: {e}")

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