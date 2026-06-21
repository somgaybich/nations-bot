from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from game.objs.structures import Link

class NationsException(Exception):
    """
    A parent class for all custom exceptions invoked by nations. Should never be invoked directly.
    Is mainly used in order to check for "expected" errors within command behavior, to prevent these
    from being raised and spamming the logs.
    """
    def __init__(self, *args):
        self.user_message = None

class CancelledException(NationsException):
    def __init__(self, action: str):
        super().__init__(f"{action} cancelled by user.")
        self.user_message = "This action was cancelled."


class NameInUse(NationsException):
    def __init__(self, name: str, object: str):
        super().__init__(f"{object.capitalize()} name '{name}' already in use")
        self.user_message = f"That {object} name is already taken!"

class UserHasNation(NationsException):
    def __init__(self, userid: int):
        super().__init__(f"ID '{userid}' is already associated with a nation")
        self.user_message = "You already have a nation!"

class NationIDNotFound(NationsException):
    def __init__(self, userid: int):
        super().__init__(f"The userid '{userid}' isn't associated with a nation")
        self.user_message = "You don't have a nation!"


class OutOfMovement(NationsException):
    def __init__(self):
        super().__init__(f"""A unit failed to move because it didn't have 
                         enough free movement""")
        self.user_message = """That unit doesn't have enough movement left 
                            this season!"""

class TooManyUnits(NationsException):
    def __init__(self):
        super().__init__(f"""A region failed to train a unit because it was
                         over its unit capacity.""")
        self.user_message = """That region does not have any more unit 
                            capacity! Either raise its tier or disband existing
                            units to train more."""

class AlreadyTraining(NationsException):
    def __init__(self):
        super().__init__(f"""A region failed to train a unit because it was
                         already training one this season.""")
        self.user_message = """That region is already training a unit! Wait
                            until next season to raise another one."""


class InvalidLocation(NationsException):
    def __init__(self, action: str, location_type: str):
        super().__init__(f"{action} failed: Cannot be done '{location_type}'")
        self.user_message = f"You can't do that {location_type}!"

class TileOutOfBounds(NationsException):
    def __init__(self, location: tuple[int, int]):
        super().__init__(f"""Tried to access {location}, which is outside the 
                         map's bounds""")
        self.user_message = f"That location is outside the map bounds!"

class TileImpassable(NationsException):
    def __init__(self, reason: str):
        super().__init__(f"Unit was unable to move to a tile because {reason}.")
        self.user_message = reason.capitalize() + "!"

class TooManyStructures(NationsException):
    def __init__(self, action: str, num_structures: int):
        super().__init__(f"""{action} failed: Region already has its max of
                         {num_structures} structures""")
        self.user_message = f"That region can't hold any more structures!"

class TIleAlreadyHadStructure(NationsException):
    def __init__(self, action: str, location: tuple[int, int]):
        super().__init__(f"""{action} failed: '{location}' already has a 
                         structure""")
        self.user_message = f"That tile already has a structure!"

class DoesNotExist(NationsException):
    def __init__(self, object_type: str, action: str, name: str):
        super().__init__(f"""{action} failed: {object_type} '{name}' does not 
                         exist""")
        self.user_message = f"Couldn't find a {object_type} named {name}!"

class NotOwned(NationsException):
    def __init__(self, action: str, location: tuple[int, int]):
        super().__init__(f"""{action} failed: User did not own the tile 
                         {location}""")
        self.user_message = f"You don't own {location}!"

class NotEnoughInfluence(NationsException):
    def __init__(self, action: str, required: int, had: int):
        super().__init__(f"""{action} failed: User needed {required} 
                         influence and had {had}""")
        self.user_message = f"""You need {required} influence to do that and 
                            only have {had}!"""

class TooManyTrades(NationsException):
    def __init__(self, trades: int, region: str):
        super().__init__(f"""Exporting failed, {region} already has its max of 
                         {trades} trades.""")
        self.user_message = f"""{region} can't handle any more than the 
                            {trades} trades it already has! Upgrade the 
                            infrastructure level or city tier for more trade 
                            capacity."""