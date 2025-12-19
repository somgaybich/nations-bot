import json
import math
import logging
from typing import Callable

from scripts.bot import bot, current_season
import scripts.errors as errors

logger = logging.getLogger(__name__)

units = {}
class Unit:
    """
    A generalized class for a military unit.
    Strength & morale are on [0, 100], exp is positive
    Type is in ["army", "fleet"]
    """
    def __init__(self, name: str, type: str, home: str, location = (0, 0), strength = 100, morale = 100, exp = 0):
        self.name = name
        self.type = type
        self.home = home
        self.location = location
        self.strength = strength
        self.morale = morale

        units.update({location: self})

def new_army(name: str, userid: int, location: tuple[int, int] = (0, 0)):
    if not isinstance(tiles[location], City):
        raise errors.InvalidLocation("Army creation", "in unsettled tiles")
    if tiles[location].owner != userid:
        raise errors.NotOwned("Army creation", location)
    if nation_list[userid].econ.influence < 1:
        return errors.NotEnoughEI("Army creation", 1, nation_list[userid].econ.influence)
    
    nation = nation_list[userid]
    nation.gov.influence -= 1
    nation.military.update({
        name: Unit(name, "army", location)
    })

def new_fleet(name: str, userid: int, location: tuple[int, int] = (0, 0)):
    if not isinstance(tiles[location], City):
        raise errors.InvalidLocation("Fleet", "in non-city tiles")
    if not "port" in tiles[location].upgrades:
        raise errors.InvalidLocation("Fleet", "in non-port settlements")
    if tiles[location].owner != userid:
        raise errors.NotOwned("Fleet creation", location)
    if nation_list[userid].econ.influence < 2:
        raise errors.NotEnoughEI("Fleet creation", 2, nation_list[userid].econ.influence)
    
    nation = nation_list[userid]
    nation.gov.influence -= 2
    nation.military.update({
        name: Unit(name, "fleet", location)
    })

class Tile:
    def __init__(self, terrain: str, location: tuple[int, int] = (0, 0), claimant: str = None, 
                 owner: str = None, upgrades: str = None):
        self.terrain = terrain
        self.location = location
        self.claimant = claimant
        self.owner = owner
        self.upgrades = upgrades if upgrades is not None else []

        tiles[location] = self
    
    def n(self) -> "Tile":
        return tiles[(self.location[0], self.location[1] - 1)]

    def nw(self) -> "Tile":
        return tiles[(self.location[0] - 1, self.location[1])]

    def sw(self) -> "Tile":
        return tiles[(self.location[0] - 1, self.location[1] - 1)]

    def s(self) -> "Tile":
        return tiles[(self.location[0], self.location[1] + 1)]

    def ne(self) -> "Tile":
        return tiles[(self.location[0] + 1, self.location[1] - 1)]

    def se(self) -> "Tile":
        return tiles[(self.location[0] + 1, self.location[1])]

    def area(self) -> list["Tile"]:
        area = [self]
        for fn in (self.n, self.nw, self.sw, self.s, self.ne, self.se):
            try:
                tile = fn()
                if tile is not None:
                    area.append(tile)
            except:
                pass
        return set(area)

    def metroarea(self) -> set["Tile"]:
        result = set()
        for tile in self.area():
            result |= tile.area()
        return result

class TileList(dict[tuple[int, int], Tile]):
    """
    A singleton class for storing tile data.
    """

    def _check_bounds(self, key: tuple[int, int]) -> None:
        try:
            x, y = key
        except (TypeError, ValueError):
            raise TypeError("Must access the tile list with a tuple of two ints")
        
        if not (-64 <= x and x >= 65 and -72 <= y and y >= 72):
            raise errors.TileOutOfBounds(key)

    def __getitem__(self, key: tuple[int, int]) -> Tile:
        self._check_bounds(key)
        super().__getitem__(key)
    
    def __setitem__(self, key: tuple[int, int], value: Tile) -> None:
        self._check_bounds(key)
        super().__setitem__(key, value)

    def __hash__(self):
        return hash(self.location)
    
    def get(self, key, default=None):
        self._check_bounds(key)
        return super().get(key, default)
tiles = TileList()

def hex_distance(a: Tile, b: Tile) -> int:
    aq, ar = a.location
    bq, br = b.location
    return (abs(aq - bq)
          + abs(aq + ar - bq - br)
          + abs(ar - br)) // 2

class City(Tile):
    def __init__(self, terrain: str, name: str, influence: int = 0, tier: int = 0, location: tuple[int, int] = (0, 0), 
                 claimant: str = None, owner: str = None, upgrades: list["UpgradeType"] = [], 
                 stability: int = 80, popularity: int = 65, inventory: list[str] = []):
        super().__init__(terrain, location, claimant, owner, upgrades)
        self.name = name
        self.influence = influence
        self.tier = tier
        self.stability = stability
        self.popularity = popularity
        self.inventory = inventory

def new_city(name: str, location: tuple[int, int], owner: int):
    """
    A helper function for making new cities.
    """
    if tiles[location].terrain == "ocean":
        raise errors.InvalidLocation("Settlement creation", "in ocean tiles")
    elif tiles[location].terrain == "high_mountains":
        raise errors.InvalidLocation("Settlement creation", "in high mountains")
    
    to_be_claimed = []
    for tile in tiles[location].area():
        if tile.owner == None:
            to_be_claimed.append(tile)
        elif tile.owner == owner:
            continue
        # Tile is owned by another player
        else:
            raise errors.NotOwned('Settlement creation', tile.location)
    
    nation = nation_list[owner]
    nation.tiles.append(to_be_claimed)
    nation.cities.update({
        name: City(tiles[location].terrain, name, location, owner, owner)
    })
    return None

class Econ:
    """
    Represents a nation's economy.
    """
    def __init__(self, nationid: str, influence: int = 4, influence_cap: int = 4):
        self.nationid = nationid
        self.influence = influence
        self.influence_cap = influence_cap

class Gov:
    """
    Represents a nation's government.
    """
    def __init__(self, nationid: str, systems: list, influence: int = 4, influence_cap: int = 4):
        self.nationid = nationid
        self.systems = systems
        self.influence = influence
        self.influence_cap = influence_cap

        # Used to store system-specific triggers i.e. new cities being built
        # Stored as tuples of (category, age)
        self.events = []

        # General-use variable for storing streaks of things for cap calculations
        # Expansionist stores a boolean of whether the minimum expansion was met last year
        # Territorialist & Urbanist use this to store PI gained last season
        self.streaks = {}
    
    def upkeep(self):
        """
        Calculates PI upkeep costs for one season.
        """
        nation = nation_list[self.nationid]
        units = len(nation.military)
        if "Militaristic" in self.systems:
            mil_cap = 0
        else:
            mil_cap = math.floor(0.2 * len(nation.military))

        if "Federalist" in self.systems:
            admin_cap = math.floor(0.3 * (nation.tiles))
        elif "Centralist" in self.systems:
            admin_cap = 0
        else:
            admin_cap = math.floor(0.2 * len(nation.tiles))
        
        espionage_cost = 0
        if not len(nation.espionage) == 0:
            for action in nation.espionage:
                espionage_cost += action['cost']

        return mil_cap + admin_cap + espionage_cost

    def event_update(self):
        """
        Updates stored events. Should be called for every government every season.
        """
        new_events = []
        for category, age in self.events:
            age += 1
            if "Pacifist" in self.systems and category == "new_army":
                continue
            if "Mercantilist" in self.systems and category == "new_trade":
                continue
            if "Territorialist" in self.systems and category == "new_tile":
                continue
            if "Urbanist" in self.systems and category == "tier_up":
                continue
            if "Isolationist" in self.systems and category == "new_trade" and current_season == 1:
                continue
            if "Expansionist" in self.systems and category == "new_tile" and current_season == 1:
                continue
            new_events.append((category, age))
            
        self.events = new_events
    
    def system_pi(self, system: str):
        """
        Calculates the PI added by a particular system.
        """
        nation = nation_list[self.nationid]

        match system:
            case "Authoritarian":
                total_stability = 0
                for city in nation.cities:
                    total_stability += city.stability
                avg_stability = total_stability / len(nation.cities)
        
                return math.floor((avg_stability - 80) / 10)
            case "Democratic":
                total_popularity = 0
                for city in nation.cities:
                    total_popularity += city.popularity
                avg_popularity = total_popularity / len(nation.cities)
                
                return math.floor((avg_popularity - 65) / 15)
            case "Militaristic":
                return math.floor(len(nation.military) / 7)
            case "Pacifist":
                if not "new_army" in self.events:
                    return 1
                else:
                    return -2 * self.events.count("new_army")
            case "Federalist":
                total_power = 0
                for subdivision in nation.subdivisions:
                    total_power += subdivision.power
                avg_power = total_power / len(nation.subdivisions)
                
                return math.floor(0.4 * avg_power)
            # Centralist doesn't add or subtract any PI
            case "Centralist":
                pass
            case "Isolationist":
                if not current_season == 0:
                    return 0
                
                if not "new_trade" in self.events:
                    return 4
                else:
                    return -2 * self.events.count("new_trade")
            case "Mercantilist":
                if "new_trade" in self.events:
                    return 1
                else:
                    return -1
            case "Expansionist":
                if current_season == 0:
                    if self.streaks["Expansionist"] == True:
                        if self.events.count("new_tile") >= 10:
                            return 0
                        self.streaks["Expansionist"] == False
                        return -6
                    if self.events.count("new_tile") >= 10:
                        self.streaks["Expansionist"] == True
                        return 6
                    else:
                        return 0
                return 0
            case "Territorialist":
                if not "new_tile" in self.events:
                    self.streaks["Territorialist"] = min(10, self.streaks["Territorialist"] + 2)
                    return self.streaks["Territorialist"]
                prev_streak = self.streaks["Territorialist"]
                self.streaks["Territorialist"] = 0
                return -prev_streak
            case "Urbanist":
                if "tier_up" in self.events:
                    self.streaks["Urbanist"] = 3 * self.events.count("tier_up")
                    return self.streaks["Urbanist"]
                prev_streak = self.streaks["Urbanist"]
                self.streaks["Urbanist"] = 0
                return -prev_streak

class Subdivision:
    """
    A segment of a nation created for easier administration.
    """
    def __init__(self, name: str, nationid: int, cities: list[City]):
        self.name = name
        self.nationid = nationid
        self.cities = cities
        self.power = 0
        self.update_power()
        
    def update_power(self):
        influence = 0
        for city in self.cities:
            influence += city.influence
        
        total_influence = nation_list[self.nationid].econ.influence_cap
        self.power = total_influence / influence

class Nation:
    """
    The top object in the hierarchy, which contains all information about a nation.
    """
    def __init__(self, name: str, userid: int, gov: Gov, econ: Econ, 
                 cities=[], tiles=[], military=[], subdivisions=[], espionage=[], dossier=""):
        self.name: str = name
        self.userid: int = userid
        self.gov: Gov = gov
        self.econ: Econ = econ
        self.subdivisions: dict[str, Subdivision] = subdivisions
        self.cities: dict[str, City] = cities
        
        self.tiles: list[Tile] = tiles
        self.military: dict[str, Unit] = military
        self.espionage = espionage #Add type annotations when we figure out how this works
        self.dossier: str = dossier

        nation_list.update({userid: self})

class NationList(dict[int, Nation]):
    """
    A singleton for storing nation data.
    """
    def __getitem__(self, key: int) -> Nation:
        if key not in self.keys():
            raise errors.NationIDNotFound(key)
        else:
            super().__getitem__(key)
nation_list = NationList()

system_opposites = {
    "Authoritarian": "Democratic",
    "Militaristic": "Pacifist",
    "Federalist": "Centralist",
    "Isolationist": "Mercantilist",
    "Expansionist": "Territorialist"
}

def new_nation(name: str, userid: int, systems: list[str]) -> Nation:
    """
    A helper function to create new nations.
    """
    if len(systems) != len(set(systems)):
        raise errors.InvalidSystems("The system list contained duplicates!")
    for system in systems:
        if system_opposites[system] in systems:
            raise errors.InvalidSystems("The system list contained opposites!")
    
    for nation in nation_list.values():
        if nation.name == name:
            raise errors.NationNameInUse(name)
        elif nation.userid == userid:
            raise errors.UserHasNation(userid)

    return Nation(name, userid, Gov(systems), Econ())

class UpgradeType:
    """
    A base class for all tile upgrades.
    """
    def __init__(self, usable_in: list[type], ei_cost: int, resource_cost: list[str], name: str, on_build: Callable = None,
                 prereq: str = '', tier_req: int = 0):
        self.usable_in = usable_in
        self.ei_cost = ei_cost
        self.resource_cost = resource_cost
        self.name = name
        self.prereq = prereq # An upgrade that needs to be built first
        self.tier_req = tier_req # The city tier that the upgrade needs to be built in
        self.on_build = on_build # A function called when building is complete

    def build(self, location: tuple[int, int], city: City, econ: Econ):
        tile = tiles[location]
        if len(city.upgrades) == 2 and not city.tier >= 2:
            raise errors.TooManyUpgrades(f"{self.name.capitalize()} creation", 2)
        if len(city.upgrades) == 3 and not city.tier == 4:
            raise errors.TooManyUpgrades(f"{self.name.capitalize()} creation", 3)
        if self.resource_cost not in city.inventory:
            raise errors.NotEnoughResources(f"{self.name.capitalize()} creation", self.resource_cost, city.inventory)
        if econ.influence < self.ei_cost:
            raise errors.NotEnoughEI(f"{self.name.capitalize()} creation", self.ei_cost, econ.influence)
        if self.usable_in == [City] and type(tile) != City:
            raise errors.InvalidLocation(f"{self.name.capitalize()} creation", f"in unsettled tiles")
        elif tile.terrain not in self.usable_in:
            raise errors.InvalidLocation(f"{self.name.capitalize()} creation", f"in {tile.terrain} tiles")
        if tile not in city.area() and city.tier != 4:
            raise errors.InvalidLocation(f"{self.name.capitalize()} creation", "outide the settlement's range")
        if tile not in city.metroarea() and city.tier == 4:
            raise errors.InvalidLocation(f"{self.name.capitalize()} creation", "outide the settlement's range")
        if not self.tier_req == 0 and isinstance(tile, city):
            if not tile.tier >= self.tier_req:
                raise errors.CityTierTooLow(f"{self.name.capitalize()} creation", tile.tier, self.tier_req)
        # This check must always be last because it has behavior attached!
        if self.prereq != '':
            if self.prereq not in tile.upgrades:
                raise errors.MissingUpgrade(f"{self.name.capitalize()} creation", self.prereq)
            
            tile.upgrades.remove(self.prereq)

        for item in self.resource_cost:
            city.inventory.remove(item)
        econ.influence -= self.ei_cost

        tiles[location].upgrades.append(self.name)

        if self.on_build != None:
            self.on_build()

def temple_built(city: City):
    city.popularity += min(100, round((city.popularity / 10) + 5))
    city.stability += min(100, round((city.stability / 20) + 5))\

upgrade_types = {
    "temple": UpgradeType(usable_in=[City], ei_cost=1, resource_cost=["stone"], name="Temple", on_build=temple_built),
    "grandtemple": UpgradeType(usable_in=[City], ei_cost=1, resource_cost=["stone"], name="Grand Temple", prereq="Temple", on_build=temple_built),
    "station": UpgradeType(usable_in=[City], ei_cost=2, resource_cost=["lumber"], name="Station"),
    "centralstation": UpgradeType(usable_in=[City], ei_cost=2, resource_cost=["lumber"], name="Central Station", prereq="Station"),
    "workshop": UpgradeType(usable_in=[City], ei_cost=1, resource_cost=["lumber", "stone"], name="Workshop"),
    "charcoalpit": UpgradeType(usable_in=[City], ei_cost=2, resource_cost=["lumber"], name="Charcoal Pit"),
    "smeltery": UpgradeType(usable_in=[City], ei_cost=2, resource_cost=["stone", "fuel"], name="Smeltery"),
    "port": UpgradeType(usable_in=[City], ei_cost=2, resource_cost=["stone", "lumber"], name="Port"),
    "foundry": UpgradeType(usable_in=[City], ei_cost=2, resource_cost=["metal", "fuel"], name="Foundry", tier_req=2)
}

class Link:
    """
    A generalized class for infrastructure connections.
    
    :var linktype: String from one of 'sea', 'simple_rail', 'quality_rail'
    :var origin: The city the link starts in. 
    :var destination: The city the link ends in. Note that order doesn't matter, but may effect pathfinding.
    :var cities: A list of both cities which are involved in the link.
    :var path: The list of tiles which make up this link.
    """

    def __init__(self, linktype: str, origin: City, destination: City, path: list[Tile]):
        self.cities = [origin, destination]
        self.path = path
        self.linktype = linktype



def serialize_object(obj):
    """Convert a Python object into a JSON-serializable dict."""
    
    # Already JSON-serializable primitives
    if isinstance(obj, (int, float, str, bool)) or obj is None:
        return obj

    # Lists / tuples / sets → list
    if isinstance(obj, (list, tuple, set)):
        return [serialize_object(item) for item in obj]

    # Dict → dict with serialized keys/values
    if isinstance(obj, dict):
        return {serialize_object(key): serialize_object(value) 
                for key, value in obj.items()}

    # User-defined objects → serialize their attributes
    if hasattr(obj, "__dict__"):
        return {key: serialize_object(value) 
                for key, value in obj.__dict__.items()}

    # Fallback: turn into string
    return str(obj)

def save() -> None:
    """
    Writes the current nation and tile data to their files for storage
    """
    try:
        with open("data\\nation_data.json", "w") as file:
            data = json.dumps(serialize_object(nation_list), indent=2)
            file.write(data)
    except Exception as e:
        logger.error(f"There was an error saving the nation data: {e}")
        logger.info(f"Logging data: {serialize_object(nation_list)}")
    
    try:
        with open("data\\tiles.json", "w") as file:
            data = json.dumps(serialize_object(tiles), indent=2)
            file.write(data)
    except Exception as e:
        logger.error(f"There was an error saving the tile data: {e}")
        logger.info(f"Logging data: {serialize_object(tiles)}")
    
    logger.info("Successfully saved tile and nation data.")

def backup() -> None:
    """
    Makes a separate backup of the data in case it is lost
    """
    try:
        with open("data\\nation_data_backup.json", "w") as file:
            data = json.dumps(serialize_object(nation_list), indent=2)
            file.write(data)
    except Exception as e:
        logger.critical(f"There was an error backing up the nation data: {e}")
        logger.info(f"Logging data: {serialize_object(nation_list)}")
    
    try:
        with open("data\\tiles_backup.json", "w") as file:
            data = json.dumps(serialize_object(tiles), indent=2)
            file.write(data)
    except Exception as e:
        logger.critical(f"There was an error backing up the nation data: {e}")
        logger.info(f"Logging data: {serialize_object(tiles)}")
    
    logger.info("Successfully backed up tile and nation data.")

# TODO: Update all this to new attributes added to accomodate new features
async def load() -> None:
    """
    Load the nation and tile data files
    WARNING: WILL OVERWRITE ALL DATA
    """
    try:
        with open("data\\nation_data.json", "r") as file:
            data = json.load(file)
            for nation in data.values():
                gov = nation["gov"]
                econ = nation["econ"]
                Nation(
                    name=nation["name"],
                    userid=nation["userid"],
                    gov=Gov(
                        gov["systems"],
                        gov["influence"],
                        gov["influence_cap"]),
                    econ=Econ(
                        econ["influence"],
                        econ["influence_cap"]
                    ),
                    cities=nation["cities"],
                    tiles=nation["tiles"],
                    military=nation["military"],
                    subdivisions=nation["subdivisions"],
                    espionage=nation["espionage"],
                    dossier=nation["dossier"])
        logger.info(f"Loaded {len(nation_list)} nations")
    except Exception as e:
        logger.critical(f"There was an error loading the nation data: {e}")
        await bot.close()
    
    try:
        with open("data\\tiles.json") as file:
            data = json.load(file)
            for location, tile in data.items():
                # Parse location from str to tuple[int, int]
                coords = location.strip("()").split(",")
                location = (int(coords[0]), int(coords[1]))
                
                # Having attribute "name" means the tile is a city
                if "name" in tile:
                    City(
                        terrain=tile["terrain"],
                        name=tile["name"],
                        influence=tile["influence"],
                        tier=tile["tier"] if "tier" in tile else 0,
                        location=location,
                        claimant=tile["claimed"] if "claimed" in tile else None,
                        owner=tile["owned"] if "owned" in tile else None,
                        upgrades=tile["upgrades"] if "upgrades" in tile else [],
                        stability=tile["stability"] if "stability" in tile else 80,
                        popularity=tile["popularity"] if "popularity" in tile else 65,
                        inventory=tile["inventory"] if "ivnentory" in tile else [])
                else:
                    Tile(terrain=tile["terrain"],
                         location=location,
                         claimant=tile["claimed"] if "claimed" in tile else None,
                         owner=tile["owned"] if "owned" in tile else None,
                         upgrades=tile["upgrades"] if "upgrades" in tile else None)
        logger.info(f"Loaded {len(tiles)} tiles")
    except Exception as e:
        logger.critical(f"There was an error loading tile data: {e}")
        await bot.close()