from typing import TYPE_CHECKING
import logging

logger = logging.getLogger(__name__)

import scripts.errors as errors

if TYPE_CHECKING:
    from game.nation import Nation
    from game.military import Unit
    from world.map import Tile
    from world.structures import Structure, Link

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

class LinkList(list["Link"]):
    def find(self, origin: str, destination: str) -> "Link":
        """
        Finds the link that connects the provided cities. If there isn't one, returns None.
        """
        for link in self:
            if link.origin == origin and link.destination == destination:
                return link
            if link.destination == origin and link.origin == destination:
                # We want this to be unordered
                # b/c origin and destination are just names
                return link
        else:
            return None

links: LinkList = LinkList()
tile_list: TileDict = TileDict()
units: list["Unit"] = []
structures: list["Structure"] = []
nation_list: NationDict = NationDict()