from dataclasses import dataclass

import world.database as db

@dataclass
class Unit:
    """
    A generalized class for a military unit.
    Strength & morale are on [0, 100], exp is positive
    Type is in ["army", "fleet"]
    """
    name: str
    """
    The name of the unit.
    """
    type: str
    """
    The type of the unit, either "army" or "fleet".
    """
    home: int
    """
    The ID of the region the unit was created in.
    """
    owner: int
    """
    The NID of the nation this unit belongs to.
    """
    movement_free: int
    """
    The number of tiles this unit is allowed to move this season.
    """
    location: tuple[int, int]
    """
    The tile this unit is located in.
    """
    strength: float = 1.0
    """
    The overall effectiveness of this unit in combat, relative to 1.0.
    """
    morale: float = 1.0
    """
    The morale of the unit's soldiers, relative to 1.0.
    """
    exp: int = 0
    """
    The number of battles this unit has been in. (Currently does nothing)
    """
    status: str = "TRAINING"
    """
    Any special state the unit is currenlty in. Currently may only be 
    'TRAINING', but future features like 'EMBARKED' are planned to use this.
    """
    id: int | None = None
    """
    The database ID of this unit.
    """
    
    async def save(self):
        await db.save_unit(self)
    
