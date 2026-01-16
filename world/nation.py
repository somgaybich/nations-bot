import logging
from discord import Color, Embed
from typing import TYPE_CHECKING

logger = logging.getLogger(__name__)

import scripts.database as db

if TYPE_CHECKING:
    from game.military import Unit
    from game.espionage import Espionage
    from world.economy import Econ
    from world.structures import Link
    from world.cities import City

class Nation:
    """
    The top object in the hierarchy, which contains all information about a nation.
    """
    def __init__(self, name: str, userid: int, econ: "Econ", cities={}, links=[], tiles=[], military=[], 
                 espionage=[], dossier={}, allies=[], color=Color.random()):
        self.name: str = name
        self.userid: int = userid
        self.econ: "Econ" = econ
        self.cities: dict[str, "City"] = cities
        self.links: list["Link"] = links
        self.tiles: list[tuple[int, int]] = tiles
        self.military: dict[str, "Unit"] = military
        self.espionage: list["Espionage"] = espionage
        self.dossier: dict = dossier
        self.allies: list[int] = allies
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