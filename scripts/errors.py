class NationsException(Exception):
    """
    A parent class for all custom exceptions invoked by nations. Should never be invoked directly.
    Is mainly used in order to check for "expected" errors within command behavior, to prevent these
    from being raised and spamming the logs.
    """
    def __init__(self, *args):
        self.user_message = None

#TODO: Add "reasoning" arguments that add a ...because... to the user_message

class CancelledException(NationsException):
    def __init__(self, action: str):
        super().__init__(f"{action} cancelled by user.")
        self.user_message = "This action was cancelled."

class NationNameInUse(NationsException):
    def __init__(self, name: str):
        super().__init__(f"Name '{name}' already in use")
        self.user_message = "That nation name is already taken!"

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
        super().__init__(f"A unit failed to move because it didn't have enough free movement")
        self.user_message = "That unit doesn't have enough movement left this season!"

class InvalidLocation(NationsException):
    def __init__(self, action: str, location_type: str):
        super().__init__(f"{action} failed: Cannot be done '{location_type}'")
        self.user_message = f"You can't do that {location_type}!"

class TileOutOfBounds(NationsException):
    def __init__(self, location: tuple[int, int]):
        super().__init__(f"Tried to access {location}, which is outside the map's bounds")
        self.user_message = f"That location is outside the map bounds!"

class TileImpassable(NationsException):
    def __init__(self, reason: str):
        super().__init__(f"Unit was unable to move to a tile because {reason}.")
        self.user_message = reason.capitalize() + "!"

class TooManyStructures(NationsException):
    def __init__(self, action: str, num_structures: int):
        super().__init__(f"{action} failed: Tile already has {num_structures} structures")
        self.user_message = f"That tile can't hold any more structures!"

class TooManyUniqueStructures(NationsException):
    def __init__(self, structure: str):
        super().__init__(f"Building {structure} failed: Nation already has a {structure}")
        self.user_message = f"You can't build more than one of those!"

class MissingStructure(NationsException):
    def __init__(self, action: str, structure: str):
        super().__init__(f"{action} failed: Tile is missing required structure '{structure}'")
        self.user_message = f"{action} needs a {structure} to be built first!"

class DoesNotExist(NationsException):
    def __init__(self, object_type: str, action: str, name: str):
        super().__init__(f"{action} failed: {object_type} '{name}' does not exist")
        self.user_message = f"Couldn't find a {object_type} at {name}!"

class CityTierTooLow(NationsException):
    def __init__(self, action: str, tier: int, required: int):
        super().__init__(f"{action} failed: Tile needs to be tier {required} and is {tier}")
        self.user_message = f"The city needs to be tier {required} to do that!"

class NotOwned(NationsException):
    def __init__(self, action: str, location: tuple[int, int]):
        super().__init__(f"{action} failed: User did not own the tile {location}")
        self.user_message = f"You don't own {location}!"

class NotEnoughInfluence(NationsException):
    def __init__(self, action: str, required: int, had: int):
        super().__init__(f"{action} failed: User needed {required} influence and had {had}")
        self.user_message = f"You need {required} influence to do that and only have {had}!"

class NotEnoughResources(NationsException):
    def __init__(self, action: str, required: list[str], had: list[str]):
        super().__init__(f"{action} failed: Needed {required} but only had {had}")
        missing_resources = ""
        for resource in required:
            if not resource in had:
                missing_resources += resource + ", "
        self.user_message = f"You don't have the resources! {missing_resources} was missing."