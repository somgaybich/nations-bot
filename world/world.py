from typing import TYPE_CHECKING
import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from game.objs.nation import Nation
    from game.objs.unit import Unit
    from game.objs.market import Market
    from game.objs.region import Region
    from game.objs.tile import Tile
    from game.objs.trade import Trade

@dataclass
class GameState:
    """
    A collection of all of the global level repositories. Records the entirety
    of the game state at any given time.
    """
    tiles: dict[tuple[int, int], "Tile"] = field(default_factory=dict)
    """
    Provides searchable access to tiles. Keys are location tuples, of form 
    (q, r), indicating the location of the tile on the map.
    """
    nations: dict[int, "Nation"] = field(default_factory=dict)
    """
    Provides searchable access to nations. Keys are the discord user ID of the
    player who created the nation.
    """
    nation_ids: dict[str, int] = field(default_factory=dict)
    """
    Maps nation names to NIDs.
    """
    regions: dict[int, "Region"] = field(default_factory=dict)
    """
    Provides searchable access to regions. Keys are unqiuely generated IDs.
    """
    region_ids: dict[str, int] = field(default_factory=dict)
    """
    Maps region names to IDs.
    """
    markets: dict[int, "Market"] = field(default_factory=dict)
    """
    Provides searchable access to markets. Keys are uniquely generated IDs.
    """
    units: dict[int, "Unit"] = field(default_factory=dict)
    """
    Provides searchable access to units. Keys are uniquely generated IDs.
    """
    unit_ids: dict[str, int] = field(default_factory=dict)
    """
    Maps unit names to IDs.
    """
    trades: dict[int, "Trade"] = field(default_factory=dict)

global state
state = GameState()

def get_state():
    """
    Returns the current game state.
    """
    return state