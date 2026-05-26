import logging
from discord import Color, Embed
from typing import TYPE_CHECKING

logger = logging.getLogger(__name__)

import scripts.database as db

if TYPE_CHECKING:
    from game.military import Unit
    from game.espionage import Espionage
    from game.economy import Econ
    from game.region import Region

class Nation:
    name: str
    """
    The name of this nation.
    """
    userid: int
    """
    The NID of this nation and the discord UID of its owner.
    """
    econ: "Econ"
    """
    This nation's economy.
    """
    regions: dict[str, "Region"]
    """
    Maps names to this nation's regions.
    """
    miltiary: dict[str, "Unit"]
    """
    Maps names to this nation's units.
    """
    espionage: list["Espionage"]
    """
    The list of ongoing espionage plots by this nation's leadership.
    """
    dossier: dict[str, str]
    """
    The dossier for this nation.\n\nWhen shown to the user, will be formatted
    as a set of paragraph blocks with key titles and value body text.
    """
    allies: list[int]
    """
    The list of NIDs this nation is allied with. Units belonging to these
    nations will assist this nation's units in combat.
    """
    color: Color
    """
    The color this nation appears on the map.
    """
    def __init__(self, name: str, userid: int, econ: "Econ", regions=None, 
                 military=None, espionage=None, dossier=None, allies=None, 
                 color=Color.random()):
        """
        :param name: The name of this nation.
        :param userid: The NID of this nation and discord UID of its owner.
        :param econ: This nation's economy.
        :param regions: Maps names to this nation's regions.
        :param miltiary: Maps names to this nation's units.
        :param espionage: The list of ongoing espionage plots by this nation's 
            leadership.
        :param dossier: The dossier for this nation.\n\nWhen shown to the user, 
            will be formatted as a set of paragraph blocks with key titles and 
            value body text.
        :param allies: The list of NIDs this nation is allied with. Units 
            belonging to these nations will assist this nation's units in 
            combat.
        :param color: The color this nation appears on the map.
        :type name: str
        :type userid: int
        :type econ: int
        :type regions: dict[str, Region]
        :type miltiary: dict[str, Unit]
        :type espionage: list[Espionage]
        :type dossier: dict[str, str]
        :type allies: list[int]
        :type color: Color
        """
        self.name: str = name
        self.userid: int = userid
        self.econ: "Econ" = econ
        self.regions: dict[str, "Region"] = (regions if regions is not None 
                                             else {})
        self.military: dict[str, "Unit"] = (military if military is not None 
                                            else {})
        self.espionage: list["Espionage"] = (espionage if espionage is not None
                                             else [])
        self.dossier: dict[str, str] = (dossier if dossier is not None
                                        else {})
        self.allies: list[int] = (allies if allies is not None
                                  else [])
        self.color: Color = color
    
    async def save(self):
        """
        Saves this nation to the database.
        """
        await db.save_nation(self)
    
    def profile(self) -> Embed:
        """
        Returns an embed formatted for this nation's profile.
        """
        message = ""
        for title, text in self.dossier.items():
            message += f"**{title}**\n{text}\n\n"
        
        return Embed(
            color=self.color,
            title=self.name,
            text=message
        )