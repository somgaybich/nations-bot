from typing import TYPE_CHECKING
import logging

logger = logging.getLogger(__name__)

import scripts.errors as errors

if TYPE_CHECKING:
    from game.nation import Nation
    from game.military import Unit
    from game.region import Region
    from game.events import Listener
    from world.map import Tile
    from world.structures import Structure

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

class RegionDict(dict[str, "Region"]):
    """
    A singleton for storing region data.
    """

tile_list: TileDict = TileDict()
"""
A dictionary mapping locations to Tile objects.
"""
units: list["Unit"] = []
"""
A list of every unit, so they can easily be searched.
"""
structures: list["Structure"] = []
"""
A list of every structure, so they can easily be searched.
"""
regions: RegionDict = RegionDict()
"""
A dictionary mapping names to Region objects.
"""
nation_list: NationDict = NationDict()
"""
A dictionary mapping NIDs to Nation objects.
"""
listeners: list["Listener"] = []
"""
A list of every event listener.
"""