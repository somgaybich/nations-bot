from typing import TYPE_CHECKING
import logging

logger = logging.getLogger(__name__)

import scripts.errors as errors

if TYPE_CHECKING:
    from game.objs.nation import Nation
    from game.objs.military import Unit
    from game.objs.market import Market, Trade
    from game.objs.region import Region
    from game.objs.events import Listener
    from game.objs.map import Tile
    from game.objs.structures import Structure

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

class MarketDict(dict[str, "Market"]):
    """
    A singleton for storing market data.
    """
    def reset(self):
        self = {}

tile_list: TileDict = TileDict()
"""
A dictionary mapping locations to :class:`Tile` objects.
"""
units: list["Unit"] = []
"""
A list of every :class:`Unit`, so they can easily be searched.
"""
structures: list["Structure"] = []
"""
A list of every :class:`Structure`, so they can easily be searched.
"""
regions: RegionDict = RegionDict()
"""
A dictionary mapping names to :class:`Region` objects.
"""
markets: MarketDict = MarketDict()
"""
A dictionary mapping names to :class:`Market` objects.
"""
trades: list["Trade"] = []
"""
A list of every :class:`Trade`, so they can easily be searched.
"""
nation_list: NationDict = NationDict()
"""
A dictionary mapping NIDs to :class:`Nation` objects.
"""
listeners: list["Listener"] = []
"""
A list of every event :class:`Listener`, so they can easily be searched.
"""