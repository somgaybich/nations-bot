import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

import world.database as db

@dataclass
class Econ:
    """
    Represents a nation's economy.
    """
    nationid: int
    """
    The NID of the parent nation.
    """
    influence: int = 2
    """
    The influence currently available.
    """
    influence_cap: int = 2
    """
    The maximum influence usable per season.
    """

    async def save(self):
        """
        Saves this economy to the database.
        """
        await db.save_economy(self)