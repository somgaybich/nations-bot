import logging
from discord import Color, Embed
from typing import TYPE_CHECKING

logger = logging.getLogger(__name__)

import scripts.database as db

if TYPE_CHECKING:
    from game.military import Unit
    from game.espionage import Espionage
    from game.economy import Econ
    from game.authority import Authority
    from game.region import Region
    from world.structures import Link

class Nation:
    """
    The top object in the hierarchy.
    """
    def __init__(self, name: str, userid: int, econ: "Econ", regions={}, 
                 links=[], military={}, espionage=[], dossier={}, allies=[], 
                 authorities={}, color=Color.random()):
        self.name: str = name
        self.userid: int = userid
        self.econ: "Econ" = econ
        self.regions: dict[str, "Region"] = regions
        self.links: list["Link"] = links
        self.military: dict[str, "Unit"] = military
        self.espionage: list["Espionage"] = espionage
        self.dossier: dict = dossier
        self.allies: list[int] = allies
        self.authorities: dict[str, "Authority"] = authorities
        self.color: Color = color
    
    async def save(self):
        await db.save_nation(self)
    
    def profile(self) -> Embed:
        message = ""
        for title, text in self.dossier.items():
            message += f"**{title}**\n{text}\n\n"
        
        return Embed(
            color=self.color,
            title=self.name,
            text=message
        )