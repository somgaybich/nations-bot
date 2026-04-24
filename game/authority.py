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
    A body that controls city administration.
    """
    def __init__(self, nationid: int, name: str, authtype: str = None, 
                 cap: int = 0, region: str = None, id=int):
        self.nationid = nationid
        self.name = name
        self.region = region
        self.id = id

        if authtype is None:
            self.authtype = random.choice(authority_cap_modifiers.keys())
        else:
            self.authtype = authtype

        if cap == 0:
            random_cap = random.randint(1, 5)
            modded_cap = random_cap + authority_cap_modifiers[self.authtype]
            self.cap = max(1, modded_cap)
        else:
            self.cap = cap
    
    async def save(self):
        await db.save_authority(self)
    
    def __str__(self):
        return f"{self.name} is a {self.authtype} authority from {self.cities[0]}."