import json
import math
import logging
from typing import Callable

from scripts.constants import current_season
import scripts.database as db
import scripts.errors as errors

logger = logging.getLogger(__name__)

units = []
class Unit:
    """
    A generalized class for a military unit.
    Strength & morale are on [0, 100], exp is positive
    Type is in ["army", "fleet"]
    """
    def __init__(self, name: str, type: str, home: str, owner: int, location = (0, 0), strength = 100, morale = 100, exp = 0, unit_id=None):
        self.id = unit_id
        self.name = name
        self.type = type
        self.home = home
        self.location = location
        self.strength = strength
        self.morale = morale
        self.exp = exp
    
    async def save(self):
        await db.save_unit(self)

async def new_army(name: str, userid: int, city_name: str):
    city = nation_list[userid].cities.get(city_name)
    if city is None:
        raise errors.DoesNotExist("city", "Army creation", city_name)
    if nation_list[userid].econ.influence < 1:
        return errors.NotEnoughEI("Army creation", 1, nation_list[userid].econ.influence)
    
    nation_list[userid].gov.influence -= 1

    new_unit = Unit(name, "army", city.location)
    nation_list[userid].military[name] = new_unit

    await nation_list[userid].save()
    await new_unit.save()

async def new_fleet(name: str, userid: int, city_name: str):
    city = nation_list[userid].cities.get(city_name)
    if city is None:
        raise errors.DoesNotExist("city", "Fleet creation", city_name)
    if not "Port" in city.upgrades:
        raise errors.MissingUpgrade("Fleet creation", "Port")
    if nation_list[userid].econ.influence < 2:
        raise errors.NotEnoughEI("Fleet creation", 2, nation_list[userid].econ.influence)
    
    nation_list[userid].gov.influence -= 2
    new_unit = Unit(name, "fleet", city.location)
    nation_list[userid].military[name] = new_unit

    await nation_list[userid].save()
    await new_unit.save()

class Tile:
    def __init__(self, terrain: str, location: tuple[int, int] = (0, 0), owner: str = None, 
                 owned: bool = False, upgrades: str = None):
        self.terrain = terrain
        self.location = location
        self.owned = owned
        self.owner = owner
        self.upgrades = upgrades if upgrades is not None else []

        tiles[location] = self
    
    async def save(self):
        await db.save_tile(self)
    
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
        
        if not (-64 <= x and x <= 65 and -72 <= y and y <= 72):
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
                 owner: str = None, upgrades: list["UpgradeType"] = [], 
                 stability: int = 80, popularity: int = 65, inventory: list[str] = []):
        super().__init__(terrain, location, owner, True, upgrades)
        self.name = name
        self.influence = influence
        self.tier = tier
        self.stability = stability
        self.popularity = popularity
        self.inventory = inventory
    
    async def save(self):
        db.save_city(self)

async def new_city(name: str, location: tuple[int, int], owner: int):
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
            to_be_claimed.append(tile.location)
        elif tile.owner == owner:
            continue
        # Tile is owned by another player
        else:
            raise errors.NotOwned('Settlement creation', tile.location)
    
    nation_list[owner].tiles.append(to_be_claimed)
    for location in to_be_claimed:
        tiles[location].owner = owner
        await tiles[location].save()

    new_city = City(tiles[location].terrain, name, location, owner, owner)
    nation_list[owner].cities[name] = new_city

    await nation_list[owner].save()
    await new_city.save()
    
    return None

class Econ:
    """
    Represents a nation's economy.
    """
    def __init__(self, nationid: str, influence: int = 4, influence_cap: int = 4):
        self.nationid = nationid
        self.influence = influence
        self.influence_cap = influence_cap

    async def save(self):
        await db.save_economy(self)

class Gov:
    """
    Represents a nation's government.
    """
    def __init__(self, nationid: str, systems: list, influence: int = 4, influence_cap: int = 4, events = [], streaks = {}):
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
    
    async def save(self):
        await db.save_government(self)
    
    def upkeep(self) -> int:
        """
        Calculates PI upkeep costs for one season.
        """
        nation = nation_list[self.nationid]
        units = len(nation.military)
        if "Militaristic" in self.systems:
            mil_cap = 0
        else:
            mil_cap = math.floor(0.2 * len(units))

        if "Federalist" in self.systems:
            admin_cap = math.floor(0.3 * len(units))
        elif "Centralist" in self.systems:
            admin_cap = 0
        else:
            admin_cap = math.floor(0.2 * len(units))
        
        espionage_cost = 0
        if not len(nation.espionage) == 0:
            for action in nation.espionage:
                espionage_cost += action['cost']

        return mil_cap + admin_cap + espionage_cost

    async def event_update(self):
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
        self.save()
    
    def system_pi(self, system: str) -> int:
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
            case _:
                raise ValueError("Invalid system (make sure it's capitalized!)")

class Subdivision:
    """
    A segment of a nation created for easier administration.
    """
    def __init__(self, name: str, nationid: int, cities: list[str]):
        self.name = name
        self.nationid = nationid
        self.cities = cities
        self.power = 0
        self.update_power()
    
    async def save(self):
        await db.save_subdivision(self)
        
    async def update_power(self):
        influence = 0
        for city_name in self.cities:
            influence += nation_list[self.nationid].cities[city_name].influence
        
        total_influence = nation_list[self.nationid].econ.influence_cap
        self.power = total_influence / influence\
        
        self.save()

class Nation:
    """
    The top object in the hierarchy, which contains all information about a nation.
    """
    def __init__(self, name: str, userid: int, gov: Gov, econ: Econ, 
                 cities={}, links=[], tiles=[], military=[], subdivisions=[], espionage=[], dossier=""):
        self.name: str = name
        self.userid: int = userid
        self.gov: Gov = gov
        self.econ: Econ = econ
        self.subdivisions: dict[str, Subdivision] = subdivisions
        self.cities: dict[str, City] = cities
        self.links: list[Link] = links
        self.tiles: list[tuple[int, int]] = tiles
        self.military: dict[str, Unit] = military
        self.espionage = espionage #Add type annotations when we figure out how this works
        self.dossier: str = dossier

        nation_list.update({userid: self})
    
    async def save(self):
        await db.save_nation(self)

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
    
    for existing_nation in nation_list.values():
        if existing_nation.name == name:
            raise errors.NationNameInUse(name)
        elif existing_nation.userid == userid:
            raise errors.UserHasNation(userid)

    nation = Nation(name, userid, Gov(systems), Econ())
    nation.save()
    return nation

class UpgradeType:
    """
    A base class for all tile upgrades.
    """
    def __init__(self, usable_in: list[type], ei_cost: int, resource_cost: list[str], name: str, prereq: str = '', tier_req: int = 0):
        self.usable_in = usable_in
        self.ei_cost = ei_cost
        self.resource_cost = resource_cost
        self.name = name
        self.prereq = prereq # An upgrade that needs to be built first
        self.tier_req = tier_req # The city tier that the upgrade needs to be built in

    async def build(self, location: tuple[int, int], city_name: str, userid: int):
        nation = nation_list.get(userid)
        if nation is None:
            raise errors.NationIDNotFound(userid)
        tile = tiles.get(location)
        city = nation.cities.get(city_name)
        if tile is None:
            raise errors.DoesNotExist("tile", f"{self.name.capitalize()} creation", location)
        if city is None:
            raise errors.DoesNotExist("city", f"{self.name.capitalize()} creation", city_name)
        if len(city.upgrades) == 2 and not city.tier >= 2:
            raise errors.TooManyUpgrades(f"{self.name.capitalize()} creation", 2)
        if len(city.upgrades) == 3 and not city.tier == 4:
            raise errors.TooManyUpgrades(f"{self.name.capitalize()} creation", 3)
        if self.resource_cost not in city.inventory:
            raise errors.NotEnoughResources(f"{self.name.capitalize()} creation", self.resource_cost, city.inventory)
        if nation_list[userid].econ.influence < self.ei_cost:
            raise errors.NotEnoughEI(f"{self.name.capitalize()} creation", self.ei_cost, nation_list[userid].econ.influence)
        if self.usable_in == [City] and type(tile) != City:
            raise errors.InvalidLocation(f"{self.name.capitalize()} creation", f"in unsettled tiles")
        elif tile.terrain not in self.usable_in:
            raise errors.InvalidLocation(f"{self.name.capitalize()} creation", f"in {tile.terrain} tiles")
        if tile not in city.area() and city.tier != 4:
            raise errors.InvalidLocation(f"{self.name.capitalize()} creation", "outide the settlement's range")
        if tile not in city.metroarea() and city.tier == 4:
            raise errors.InvalidLocation(f"{self.name.capitalize()} creation", "outide the settlement's range")
        if not self.tier_req == 0 and location == city.location:
            if not tile.tier >= self.tier_req:
                raise errors.CityTierTooLow(f"{self.name.capitalize()} creation", tile.tier, self.tier_req)
        # This check must always be last because it has behavior attached!
        if self.prereq != '':
            if self.prereq not in tile.upgrades:
                raise errors.MissingUpgrade(f"{self.name.capitalize()} creation", self.prereq)
            
            tiles[location].upgrades.remove(self.prereq)
            await tiles[location].save()

        for item in self.resource_cost:
            nation_list[userid].cities[city_name].inventory.remove(item)
        nation_list[userid].econ.influence -= self.ei_cost

        tiles[location].upgrades.append(self.name)

        if self.name == "Temple" or self.name == "Grand Temple":
            nation_list[userid].cities[city_name].popularity += min(100, round((nation_list[userid].cities[city_name].popularity / 10) + 5))
            nation_list[userid].cities[city_name].stability += min(100, round((nation_list[userid].cities[city_name].stability / 20) + 5))

        await nation_list[userid].save()
        await nation_list[userid].cities[city_name].save()
        await tiles[location].save()

upgrade_types = {
    "temple": UpgradeType(usable_in=[City], ei_cost=1, resource_cost=["stone"], name="Temple"),
    "grandtemple": UpgradeType(usable_in=[City], ei_cost=1, resource_cost=["stone"], name="Grand Temple", prereq="Temple"),
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
    
    :var linktype: String from one of 'stone', 'sea', 'simple_rail', 'quality_rail'
    :var origin: The name of the city the link starts in. 
    :var destination: The name of the city the link ends in. Note that order doesn't matter, but may effect pathfinding.
    :var path: The list of locations which make up this link.
    :var owner: The userid of the nation which owns this link.
    """

    def __init__(self, linktype: str, origin: str, destination: str, path: list[tuple[int, int]], owner: int, link_id = None):
        self.origin = origin
        self.destination = destination
        self.path = path
        self.owner = owner
        self.linktype = linktype
    
    #TODO: Implement this
    def build_free(self):
        """
        An alternate form of build that doesn't cost anything, mainly for use in load().
        """
        pass

    def build(self):
        length = len(self.path)
        match self.linktype:
            case "stone":
                ei_cost = math.ceil(length / 2)
                metal_cost = 0
                stone_cost = math.ceil(length / 5)
            case "sea":
                ei_cost = math.ceil(length / 5)
                metal_cost = 0
                stone_cost = 0
            case "simple_rail":
                ei_cost = length
                metal_cost = math.ceil(length / 3)
                stone_cost = 0
            case "quality_rail":
                ei_cost = length * 2
                metal_cost = math.ceil(length / 2)
                stone_cost = 0

        resources = nation_list[self.owner].cities[self.origin].inventory + nation_list[self.owner].cities[self.destination].inventory
        if resources.count("metal") < metal_cost:
            raise errors.NotEnoughResources("Link construction", ["metal"] * metal_cost, resources)
        if resources.count("stone") < stone_cost:
            raise errors.NotEnoughResources("Link construction", ["stone"] * stone_cost, resources)

        if nation_list[self.owner].econ.influence < ei_cost:
            raise errors.NotEnoughEI("Link construction", ei_cost, nation_list[self.owner].econ.influence)
        metal_remaining = metal_cost
        last = 0
        while metal_remaining > 0:
            if last == 0:
                if "metal" in nation_list[self.owner].cities[self.origin].inventory:
                    nation_list[self.owner].cities[self.origin].inventory.remove("metal")
                last = 1
            elif last == 1:
                if "metal" in nation_list[self.owner].cities[self.destination].inventory:
                    nation_list[self.owner].cities[self.destination].inventory.remove("metal")
                last = 0
            metal_remaining -= 1
            if not ("metal" in nation_list[self.owner].cities[self.origin].inventory) and not ("metal" in nation_list[self.owner].cities[self.destination].inventory) and metal_remaining > 0:
                raise errors.NotEnoughResources("Link construction", ["metal"] * metal_cost, resources)
        
        stone_remaining = stone_cost
        last = 0
        while stone_remaining > 0:
            if last == 0:
                if "stone" in nation_list[self.owner].cities[self.origin].inventory:
                    nation_list[self.owner].cities[self.origin].inventory.remove("stone")
                last = 1
            elif last == 1:
                if "stone" in nation_list[self.owner].cities[self.destination].inventory:
                    nation_list[self.owner].cities[self.destination].inventory.remove("stone")
                last = 0
            stone_remaining -= 1
            if not ("stone" in nation_list[self.owner].cities[self.origin].inventory) and not ("stone" in nation_list[self.owner].cities[self.destination].inventory) and stone_remaining > 0:
                raise errors.NotEnoughResources("Link construction", ["stone"] * stone_cost, resources)

        nation_list[self.owner].econ.influence -= ei_cost

        for location in self.path:
            tiles[location].upgrades.append(self.linktype)
            tiles[location].save()
        nation_list[self.owner].links.append(self)

        nation_list[self.owner].save()
        nation_list[self.owner].cities[self.origin].save()
        nation_list[self.owner].cities[self.destination].save()

def load_terrain():
    """
    Loads terrain data from tiles.json into the tiles singleton.
    """
    logger.info("Starting terrain load...")
    with open("data/tiles.json", "r") as f:
        terrain_data = json.load(f)
    
    for location, tile_info in terrain_data.items():
        location = tuple(map(int, location.strip("()").split(", ")))
        terrain = tile_info['terrain']
        Tile(terrain, location)

    logger.info("Terrain load complete")

async def load():
    """
    Reloads all game state data and reinstantiates from the database. Use will instantly clear any runtime data not protected by a save.
    """
    logger.warning("Clearing nation data")
    nation_list.clear()
    units.clear()
    tiles.clear()
    
    logger.info("Starting game data load...")
    nations_data = await db.load_nations_rows()
    for row in nations_data:
        nation = Nation(
            name=row["name"],
            userid=row["id"],
            gov=None,      # filled later
            econ=None,     # filled later
            dossier=row["dossier"],
        )
        nation_list[row["id"]] = nation

    governments_data = await db.load_governments_rows()
    for row in governments_data:
        gov = Gov(
            nationid=row["nationid"],
            systems=json.loads(row["systems"]),
            influence=row["influence"],
            influence_cap=row["influence_cap"],
        )
        gov.streaks = json.loads(row["streaks"])
        nation_list[row["nationid"]].gov = gov

    economies_data = await db.load_economies_rows()
    for row in economies_data:
        econ = Econ(
            nationid=row["nationid"],
            influence=row["influence"],
            influence_cap=row["influence_cap"],
        )
        nation_list[row["nationid"]].econ = econ

    tiles_data = await db.load_tiles_rows()
    for row in tiles_data:
        Tile(
            terrain=row["terrain"],
            location=(row["x"], row["y"]),
            owner=row["owner"],
            owned=row["owned"],
            upgrades=json.loads(row["upgrades"]) if row["upgrades"] else [],
        )

    cities_data = await db.load_cities_rows()
    for row in cities_data:
        nation_list[row["owner"]].cities[row["name"]] = City(
            terrain=tiles[(row["x"], row["y"])].terrain,
            name=row["name"],
            influence=row["influence"],
            tier=row["tier"],
            location=(row["x"], row["y"]),
            owner=row["owner"],
            stability=row["stability"],
            popularity=row["popularity"],
            inventory=json.loads(row["inventory"]),
        )

    units_data = await db.load_units_rows()
    for row in units_data:
        Unit(
            name=row["name"],
            type=row["unit_type"],
            home=row["home"],
            location=(row["x"], row["y"]),
            strength=row["strength"],
            morale=row["morale"],
            exp=row["exp"],
            owner=row["owner"],
            unit_id=row["id"],
        )

    links_data = await db.load_links_rows()
    for row in links_data:
        nation_list[row["owner"]].links.append(Link(
            linktype=row["linktype"],
            origin=row["origin"],
            destination=row["destination"],
            path=json.loads(row["path"]),
            owner=row["owner"],
            link_id=row["id"]
        ))

    subdivisions_data = await db.load_subdivisions_rows()
    for row in subdivisions_data:
        nation_list[row["nationid"]].subdivisions[row["name"]] = Subdivision(
            name=row["name"],
            nationid=row["nationid"],
            cities=[],  # populated next
        )
    
    logger.info("Loaded game data")