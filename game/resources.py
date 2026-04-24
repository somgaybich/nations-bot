import logging

logger = logging.getLogger(__name__)

class Resource():
    def __init__(self, name: str, origin: str, located_at: str,
                 used_in: tuple[int, int] = None):
        self.name = name
        self.origin = origin
        self.located_at = located_at
        self.used_in = used_in

    def encode(self):
        return {
            "name": self.name,
            "origin": self.origin,
            "located_at": self.located_at,
            "used_in": self.used_in
        }
