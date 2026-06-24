import logging
from discord import Color
from typing import TYPE_CHECKING
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

import world.database as db

if TYPE_CHECKING:
    from game.objs.economy import Econ

@dataclass
class Nation:
    name: str
    """
    The name of this nation.
    """
    userid: int
    """
    The NID of this nation and the discord UID of its owner.
    """
    econ: "Econ" = None
    """
    This nation's economy.
    """
    regions: list[int] = field(default_factory=list)
    """
    The IDs of this nation's regions.
    """
    units: list[int] = field(default_factory=list)
    """
    The IDs of this nation's units.
    """
    # espionage: list["Espionage"]
    # """
    # The list of ongoing espionage plots by this nation's leadership.
    # """
    dossier: dict[str, str] = field(default_factory=dict)
    """
    The dossier for this nation.\n\nWhen shown to the user, will be formatted
    as a set of paragraph blocks with key titles and value body text.
    """
    allies: list[int] = field(default_factory=list)
    """
    The list of NIDs this nation is allied with. Units belonging to these
    nations will assist this nation's units in combat.
    """
    trades: list[int] = field(default_factory=list)
    """
    The list of trade IDs that connect to this nation.
    """
    color: Color = field(default_factory=Color.random)
    """
    The color this nation appears on the map.
    """
    
    async def save(self):
        """
        Saves this nation to the database.
        """
        await db.save_nation(self)