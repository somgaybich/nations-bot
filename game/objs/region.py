from dataclasses import dataclass, field
import world.database as db
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from game.data.industries import IndustryType

@dataclass
class Region:
    """
    A region including a central ctiy and a mutable group of tiles around it.
    Effectively the true unit of land.
    """
    name: str
    """
    The name of the central city of the region, and also the region itself.
    """
    location: tuple[int, int]
    """
    The location of this region's central city.
    """
    owner: int
    """
    The NID of the nation that controls this region.
    """
    tiles: list[tuple[int, int]]
    """
    The list of tile coordinates that belong to this region.
    """
    id: int | None = None
    """
    The database ID of this region.
    """
    city_tier: int = 0
    """
    The tier of this region's central city. Starts at 0 and ranges to 4. Based
    on population.
    """
    population: float = 1.0
    """
    A measure of the size of this region's central city. Growth is based on
    surplus of needed resources. Not an actual population count, can be thought
    of as "the amount of people that consume x units of food."
    """
    is_capital: bool = False
    """
    Whether this region is the capital of its nation.
    """
    market: int | None = field(default=None, init=False)
    """
    The ID of the market this region belongs to. Can occasionally be None only 
    if markets are currently being rebuilt.
    """
    industries: list["IndustryType"] = field(default_factory=list)
    """
    The industries in this region. See :class:`game.industry.IndustryType`
    """
    luxury: str | None = None
    """
    The rare luxury available to this region, if any. Should be generated when
    the region is created, and allows the construction of the corresponding
    industry. 
    """

    async def save(self):
        """
        Saves this region to the database.
        """
        await db.save_region(self)