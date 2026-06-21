from dataclasses import dataclass, field
import json

@dataclass
class Terrain:
    """
    Holds the terrain data of a particular tile.
    """
    biome: str
    """
    The climate biome of the parent tile.
    """
    is_land: bool
    """
    Whether this tile is land or not.
    """
    is_water: bool
    """
    Whether this tile is water or not.
    """
    difficulty: int
    """
    The amount of free movement a unit loses for passing through this tile.
    """
    straits: list[int] = field(default_factory=list)
    """
    Any straits that might be adjacent to this tile. Corresponds to a side of 
    this tile counting counterclockwise starting from the NE side with index 0.
    """
    ores: dict[str, float] = field(default_factory=dict)
    """
    The richnesses of ores in this tile. Has keys "iron", "copper", "gold", and
    "coal", "oil".
    """
    
    def data(self):
        """
        Returns a json-safe version of this terrain data to be saved
        in the database.
        """
        return json.dumps([self.biome, self.is_land, self.is_water, 
                           self.difficulty, self.straits, self.ores])