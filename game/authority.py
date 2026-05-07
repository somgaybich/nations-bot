import logging
import random

logger = logging.getLogger(__name__)

from game.events import new_listener, authority_listeners
import scripts.database as db

# Authority concepts:
# Mercantile
#    * Loses and gains co-op based on trade
#    - Boosts trade capacity
#    - Lowers unit cap
# Industrial
#    * Same co-op mechanics as Mercantile
#    - Much higher chance of discovering luxuries
# Militaristic
#    * Loses and gains co-op based on whether there are units in region
#    - Boosts unit effectiveness
#    - Lowers trade capacity
# Civic
#    * Gains co-op slowly over time, loses from interference of any kind
#    - Reduces needed luxuries for tiers by 1
#    - Lowers unit cap
# Corrupt
#    * Loses and gains co-op like civic but faster
#    * Only arises from old authorities collapsing
#    - Boosts inf by 2
#    - Lowers unit cap and trade cap
# Religious
#    * Very stable, doesn't lose co-op passively and resists invasions
#    - Resistance to changes 
# Populist
#    * Extremely unstable, gradually loses co-op over time. When it collapses,
#      the region authority is re-rolled.
#    - Boosts inf output by 1 per tier, boosts trade cap, boosts unit cap

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
    valid values and relevant behavior.
    """
    region: str
    """
    The name of the region this authority controls.
    """
    cooperation: float
    """
    How compliant this authority is with the government of its parent nation.
    Ranges from 0 to 1. Informs revolt behavior.
    """
    id: int | None
    """
    The database ID of the region. Generally shouldn't be touched, use the name 
    as an identifier instead.
    """

    def __init__(self, nationid: int, name: str, authtype: str = None, 
                 region: str = None, cooperation: int = 0.8, 
                 id: int | None = None):
        """
        :param nationid: The NID of the parent nation.
        :param name: The name of this authority.
        :param authtype: The type of this authority. See comments above the 
            class definition for valid values.
        :param region: The name of the region this authority controls.
        :param cooperation: How compliant this authority is with the government
            of its parent nation. Ranges from 0 to 1. Informs revolt behavior.
        :param id: The database ID of the region. Do not assign for new
            authorities, handled by SQLite.
        :type nationid: int
        :type name: str
        :type authtype: str
        :type region: str
        :type id: int
        """
        self.nationid = nationid
        self.name = name
        self.region = region
        self.cooperation = cooperation
        self.id = id

        if authtype is None:
            # FIXME: Use logic instead of randomly choosing
            self.authtype = random.choice(authority_listeners.keys())
        else:
            self.authtype = authtype

        new_listener(self, authority_listeners[authtype])
    
    async def save(self):
        """
        Saves this authority to the database.
        """
        await db.save_authority(self)
    
    def revolting(self):
        """
        Makes a roll on this authority's calculated revolt chance. Should only
        be called in the global tick function.
        """
        if self.cooperation <= 0:
            return True

        chance = 4 / (self.cooperation - 1.6) + 3.5

        if random.random() < chance:
            return True
        else:
            return False

    def __str__(self):
        return f"""{self.name} is the {self.authtype} authority 
                of {self.region}."""