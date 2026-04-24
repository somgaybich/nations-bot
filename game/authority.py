import logging
import random

logger = logging.getLogger(__name__)

from game.constants import authority_cap_modifiers

import scripts.database as db

# Authority concepts:
# Militaristic - Effectiveness bonus for units from and in administered area / lower base stability
# Aristocratic - Cities with luxuries will gain stability / those without will lose it
# Populist - Cities gain stability slower over time / are more likely to revolt
# Legalist - Very low revolt chance / inf gain is lowered

class Authority:
    """
    A body that controls region administration.
    """
    nationid: int
    """
    The NID of the parent nation.
    """
    name: str
    """
    The name of this authority.
    """
    authtype: str
    """
    The type of this authority. See comments above the class definition for 
    valid values.
    """
    region: str
    """
    The name of the region this authority controls.
    """
    id: int
    """
    The database ID of the region. Generally shouldn't be touched, use the name 
    as an identifier instead.
    """

    def __init__(self, nationid: int, name: str, authtype: str = None, 
                 region: str = None, id: int | None = None):
        """
        :param nationid: The NID of the parent nation.
        :param name: The name of this authority.
        :param authtype: The type of this authority. See comments above the 
            class definition for valid values.
        :param region: The name of the region this authority controls.
        :param id: The database ID of the region. Do not assign for new
            authorities, as this is handled by SQLite.
        :type nationid: int
        :type name: str
        :type authtype: str
        :type region: str
        :type id: int
        """
        self.nationid = nationid
        self.name = name
        self.region = region
        self.id = id

        if authtype is None:
            self.authtype = random.choice(authority_cap_modifiers.keys())
        else:
            self.authtype = authtype
    
    async def save(self):
        """
        Saves this authority to the database.
        """
        await db.save_authority(self)
    
    def __str__(self):
        return f"{self.name} is a {self.authtype} authority from {self.cities[0]}."