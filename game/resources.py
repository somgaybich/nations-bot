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
    origin: tuple[int, int]
    """
    The location of the structure that produced this item.
    """
    located_at: str
    """
    The region this item is currently located in.
    """
    used_in: tuple[int, int]
    """
    The structure this item is being consumed in. Defaults to None if not used.
    If an item is used in improving a city's tier, this will still be None, but
    the city will downgrade on the next cycle.
    """
    path: list[str]
    """
    The names of the regions this item passed through to get to its
    location. Because of how these are assigned, includes the source region but
    excludes the current location.
    """

    def __init__(self, name: str, origin: tuple[int, int], located_at: str,
                 used_in: tuple[int, int] = None, path: list[str] = []):
        """
        :param name: The name of this item's type.
        :param origin: The location of the structure that produced this item.
        :param located_at: The region this item is currently located in.
        :param used_in: The structure this item is being consumed in. Defaults 
            to None if not used. If an item is used in improving a city's 
            tier, this will still be None, but the city will downgrade on the 
            next cycle.
        :param path: The names of the regions this item passed through to get 
            to its location. Because of how these are assigned, includes the 
            source region but excludes the current location.
        :type name: str
        :type origin: tuple[int, int]
        :type located_at: str
        :type used_in: tuple[int, int]
        """
        self.name = name
        self.origin = origin
        self.located_at = located_at
        self.used_in = used_in
        self.path = path

    def encode(self):
        """
        Encodes this item's data so it can safely be saved.
        """
        return {
            "name": self.name,
            "origin": self.origin,
            "located_at": self.located_at,
            "used_in": self.used_in,
            "path": self.path
        }
