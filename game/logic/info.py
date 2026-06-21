from discord import Embed
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from game.objs.nation import Nation

def profile(nation: "Nation") -> Embed:
    """
    Takes apart a nation's dossier and formats it nicely into an Embed.
    """
    message = ""
    for title, text in nation.dossier.items():
        message += f"**{title}**\n{text}\n\n"
    
    return Embed(
        color=nation.color,
        title=nation.name,
        text=message
    )