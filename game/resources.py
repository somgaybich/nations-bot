import logging

logger = logging.getLogger(__name__)

class Resource():
    """
    An item.
    """
    name: str
    """
    The name of the item's type.
    """
    origin: str
    """
    The region that produced this item.
    """
    located_at: str
    """
    The region this item is currently located in.
    """
    path: list[str]
    """
    The names of the regions this item passed through to get to its
    location. Because of how these are assigned, includes the source region but
    excludes the current location.
    """

    def __init__(self, name: str, origin: str, located_at: str,
                 used_in: tuple[int, int] = None, path: list[str] = []):
        """
        :param name: The name of this item's type.
        :param origin: The region that produced this item.
        :param located_at: The region this item is currently located in.
        :param path: The names of the regions this item passed through to get 
            to its location. Because of how these are assigned, includes the 
            source region but excludes the current location.
        :type name: str
        :type origin: tuple[int, int]
        :type located_at: str
        """
        self.name = name
        self.origin = origin
        self.located_at = located_at
        self.path = path

    def encode(self):
        """
        Encodes this item's data so it can safely be saved.
        """
        return {
            "name": self.name,
            "origin": self.origin,
            "located_at": self.located_at,
            "path": self.path
        }
