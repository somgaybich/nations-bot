import logging

from world.structures import Link

logger = logging.getLogger(__name__)

class Resource():
    def __init__(self, name: str, origin: tuple[int, int], located_at: str,
                 path: list[Link] = [], 
                 used_in: tuple[int, int] | Link = None):
        self.name = name
        self.origin = origin
        self.located_at = located_at
        self.path = path
        self.used_in = used_in

    def encode(self):
        if isinstance(self.used_in, Link):
            encoded_used = self.used_in.encode()
        else:
            encoded_used = self.used_in
        return {
            "name": self.name,
            "origin": self.origin,
            "located_at": self.located_at,
            "path": [link.encode() for link in self.path],
            "used_in": encoded_used
        }
