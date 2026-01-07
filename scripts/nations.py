import json
import math
import logging
import random
from discord import Embed, Color

from scripts.constants import current_season, update_season, json_terrain
import scripts.database as db
import scripts.errors as errors

logger = logging.getLogger(__name__)

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
        self.owner = owner
        self.location = location
        self.strength = strength
        self.morale = morale
        self.exp = exp
    
    async def save(self):
        await db.save_unit(self)
units: list[Unit] = []

async def new_army(name: str, userid: int, city_name: str):
    nation = nation_list[userid]
    city = nation.cities.get(city_name)
    econ = nation.econ

    if city is None:
        raise errors.DoesNotExist("city", "Army creation", city_name)
    if econ.influence < 1:
        return errors.NotEnoughEI("Army creation", 1, econ.influence)
    
    econ.influence -= 1
    new_unit = Unit(name=name, type="army", location=city.location)
    nation.military[name] = new_unit

    await nation.save()
    await econ.save()
    await new_unit.save()

async def new_fleet(name: str, userid: int, city_name: str):
    nation = nation_list[userid]
    city = nation.cities.get(city_name)
    econ = nation.econ

    if city is None:
        raise errors.DoesNotExist("city", "Fleet creation", city_name)
    if not "Port" in city.structures:
        raise errors.MissingStructure("Fleet creation", "Port")
    if econ.influence < 2:
        raise errors.NotEnoughEI("Fleet creation", 2, econ.influence)
    
    econ.influence -= 2
    new_unit = Unit(name=name, type="fleet", location=city.location)
    nation.military[name] = new_unit

    await nation.save()
    await econ.save()
    await new_unit.save()

class Tile:
    def __init__(self, terrain: str, location: tuple[int, int] = (0, 0), owner: str = None, 
                 owned: bool = False, structures: str = None):
        self.terrain = terrain
        self.location = location
        self.owned = owned
        self.owner = owner
        self.structures = structures if structures is not None else []
    
    async def save(self):
        await db.save_tile(self)
    
    def n(self) -> "Tile":
        return tile_list[(self.location[0], self.location[1] - 1)]

    def nw(self) -> "Tile":
        return tile_list[(self.location[0] - 1, self.location[1])]

    def sw(self) -> "Tile":
        return tile_list[(self.location[0] - 1, self.location[1] - 1)]

    def s(self) -> "Tile":
        return tile_list[(self.location[0], self.location[1] + 1)]

    def ne(self) -> "Tile":
        return tile_list[(self.location[0] + 1, self.location[1] - 1)]

    def se(self) -> "Tile":
        return tile_list[(self.location[0] + 1, self.location[1])]

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

class TileDict(dict[tuple[int, int], Tile]):
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
        try:
            return super().__getitem__(key)
        except Exception as e:
            logger.warning(f"Failed to getitem tile at {key}: {e}")
    
    def __setitem__(self, key: tuple[int, int], value: Tile) -> None:
        self._check_bounds(key)
        try:
            super().__setitem__(key, value)
        except Exception as e:
            logger.warning(f"Failed to set tile at {key}: {e}")
    
    def get(self, key, default=None):
        self._check_bounds(key)
        try:
            return super().get(key, default)
        except Exception as e:
            logger.warning(f"Failed to get tile at {key}: {e}")
tile_list = TileDict()

def hex_distance(a: Tile, b: Tile) -> int:
    aq, ar = a.location
    bq, br = b.location
    return (abs(aq - bq)
          + abs(aq + ar - bq - br)
          + abs(ar - br)) // 2

class City(Tile):
    def __init__(self, terrain: str, name: str, influence: int = 0, tier: int = 0, location: tuple[int, int] = (0, 0), 
                 owner: str = None, structures: list["StructureType"] = [], 
                 stability: int = 80, popularity: int = 65, inventory: list[str] = []):
        super().__init__(terrain, location, owner, True, structures)
        self.name = name
        self.influence = influence
        self.tier = tier
        self.stability = stability
        self.popularity = popularity
        self.inventory = inventory
    
    async def save(self):
        await db.save_city(self)
    
    def luxury_count(self) -> int:
        luxuries = []
        for item in self.inventory:
            if item.startswith("luxurygoods") and item not in luxuries:
                luxuries.append(item)
        return len(luxuries)

    def calculate_tier(self) -> int:
        inventory = self.inventory
        raw_inventory = [item.split("_")[0] for item in inventory]
        
        if "lumber" in inventory and "food" in inventory:
            if "lumber" in inventory and "fuel" in inventory and raw_inventory.count("food") >= 2:
                if raw_inventory.count("lumber") >= 2 and raw_inventory.count("food") >= 3 and raw_inventory.count("fuel") >= 2 and self.luxury_count() >= 1:
                    if raw_inventory.count("lumber") >= 3 and raw_inventory.count("food") >= 5 and raw_inventory.count("fuel") >= 3 and self.luxury_count() >= 2:
                        return 4
                    return 3
                return 2
            return 1
        else:
            return 0

async def new_city(name: str, location: tuple[int, int], owner: int):
    """
    A helper function for making new cities.
    """
    if tile_list[location].terrain == "ocean":
        raise errors.InvalidLocation("Settlement creation", "in ocean tiles")
    elif tile_list[location].terrain == "high_mountains":
        raise errors.InvalidLocation("Settlement creation", "in high mountains")
    
    to_be_claimed = []
    for tile in tile_list[location].area():
        if tile.owner == None:
            to_be_claimed.append(tile.location)
        elif tile.owner == owner:
            continue
        # Tile is owned by another player
        else:
            raise errors.NotOwned('Settlement creation', tile.location)
    
    nation_list[owner].tiles.append(to_be_claimed)
    for location in to_be_claimed:
        tile_list[location].owner = owner
        await tile_list[location].save()

    new_city = City(terrain=tile_list[location].terrain, name=name, location=location, owner=owner)
    nation_list[owner].cities[name] = new_city

    await nation_list[owner].save()
    await new_city.save()
    
    return None

class Econ:
    """
    Represents a nation's economy.
    """
    def __init__(self, nationid: int, influence: int = 2, influence_cap: int = 2):
        self.nationid = nationid
        self.influence = influence
        self.influence_cap = influence_cap

    async def save(self):
        await db.save_economy(self)
    
    def calculate_cap(self) -> int:
        cap = 1
        nation = nation_list[self.nationid]
        for city in nation.cities.values():
            cap += city.tier + 1
            if "district" in city.structures:
                cap += 2
            
            luxuries = city.luxury_count()
            if city.tier == 3:
                luxuries -= 1
            elif city.tier == 4:
                luxuries -= 2
            cap += luxuries
        
        for link in nation.links:
            match link.linktype:
                case "stone":
                    cap += 1
                case "sea":
                    cap += 1
                case "simple_rail":
                    cap += 3
                case "quality_rail":
                    cap += 5
            
            structures = nation.cities[link.origin].structures + nation.cities[link.destination].structures
            for structure in structures:
                if structure == "station" and link.linktype == "simple_rail" or link.linktype == "quality_rail":
                    cap += 1
                if structure == "port" and link.linktype == "sea":
                    cap += 2

        return 1

class Espionage:
    def __init__(self, investment, espionage_type, target):
        self.investment = investment
        self.success_chance = 0.1 + (0.05 * (investment - 1))
        self.reveal_chance = 0.9 - (0.04 * (investment - 1))
        self.espionage_type = espionage_type
        self.target = target
    
    def roll(self):
        if random.random() > self.success_chance:
            if self.espionage_type == "spy":
                pass
                # do spy stuff?
            elif self.espionage_type == "assassin":
                pass
                # do assassin stuff?
        if random.random() > self.reveal_chance:
            pass
            # do reveal stuff?

class Nation:
    """
    The top object in the hierarchy, which contains all information about a nation.
    """
    def __init__(self, name: str, userid: int, econ: Econ, 
                 cities={}, links=[], tiles=[], military=[], espionage=[], dossier={}, color=Color.random()):
        self.name: str = name
        self.userid: int = userid
        self.econ: Econ = econ
        self.cities: dict[str, City] = cities
        self.links: list[Link] = links
        self.tiles: list[tuple[int, int]] = tiles
        self.military: dict[str, Unit] = military
        self.espionage: list[Espionage] = espionage
        self.dossier: dict = dossier
        self.color: Color = color
    
    async def save(self):
        await db.save_nation(self)
    
    def profile(self) -> Embed:
        message = ""
        for title, text in self.dossier.items():
            message += f"**{title}**\n{text}\n\n"
        
        return Embed(
            color=self.color,
            title=self.name,
            text=message
        )

class NationDict(dict[int, Nation]):
    """
    A singleton for storing nation data.
    """
    def __getitem__(self, key: int) -> Nation:
        if key not in self.keys():
            raise errors.NationIDNotFound(key)
        else:
            return super().__getitem__(key)
nation_list = NationDict()

async def new_nation(name: str, userid: int) -> Nation:
    """
    A helper function to create new nations.
    """
    for existing_nation in nation_list.values():
        if existing_nation.name == name:
            raise errors.NationNameInUse(name)
        elif existing_nation.userid == userid:
            raise errors.UserHasNation(userid)
    
    econ = Econ(userid)
    nation = Nation(name=name, userid=userid, econ=econ)
    nation_list[userid] = nation
    
    await nation.save()
    await econ.save()
    return nation

class StructureType:
    """
    A base class for all tile structures.
    """
    def __init__(self, usable_in: list[type], inf_cost: int, resource_cost: list[str], name: str, prereq: str = '', tier_req: int = 0):
        self.usable_in = usable_in
        self.inf_cost = inf_cost
        self.resource_cost = resource_cost
        self.name = name
        self.prereq = prereq # An structure that needs to be built first
        self.tier_req = tier_req # The city tier that the structure needs to be built in

    async def build(self, location: tuple[int, int], city_name: str, userid: int):
        nation = nation_list.get(userid)
        if nation is None:
            raise errors.NationIDNotFound(userid)
        tile = tile_list.get(location)
        city = nation.cities.get(city_name)
        if tile is None:
            raise errors.DoesNotExist("tile", f"{self.name} creation", location)
        if city is None:
            raise errors.DoesNotExist("city", f"{self.name} creation", city_name)
        if len(city.structures) == 2 and not city.tier >= 2:
            raise errors.TooManyStructures(f"{self.name} creation", 2)
        if len(city.structures) == 3 and not city.tier == 4:
            raise errors.TooManyStructures(f"{self.name} creation", 3)
        if self.resource_cost not in city.inventory:
            raise errors.NotEnoughResources(f"{self.name} creation", self.resource_cost, city.inventory)
        if nation_list[userid].econ.influence < self.inf_cost:
            raise errors.NotEnoughEI(f"{self.name} creation", self.inf_cost, nation_list[userid].econ.influence)
        if self.usable_in == [City] and type(tile) != City:
            raise errors.InvalidLocation(f"{self.name} creation", f"in unsettled tiles")
        elif tile.terrain not in self.usable_in:
            raise errors.InvalidLocation(f"{self.name} creation", f"in {tile.terrain} tiles")
        if tile not in city.area() and city.tier != 4:
            raise errors.InvalidLocation(f"{self.name} creation", "outide the settlement's range")
        if tile not in city.metroarea() and city.tier == 4:
            raise errors.InvalidLocation(f"{self.name} creation", "outide the settlement's range")
        if not self.tier_req == 0 and location == city.location:
            if not tile.tier >= self.tier_req:
                raise errors.CityTierTooLow(f"{self.name} creation", tile.tier, self.tier_req)
        # This check must always be last because it has behavior attached!
        if self.prereq != '':
            if self.prereq not in tile.structures:
                raise errors.MissingStructure(f"{self.name} creation", self.prereq)
            for city in nation.cities.values():
                if self.name in city.structures:
                    raise errors.TooManyUniqueStructures(self.name)
            
            tile.structures.remove(self.prereq)
            await tile.save()

        for item in self.resource_cost:
            city.inventory.remove(item)
        nation.econ.influence -= self.inf_cost

        tile.structures.append(self.name)

        if self.name == "Temple" or self.name == "Grand Temple":
            city.popularity += min(100, round((nation_list[userid].cities[city_name].popularity / 10) + 5))
            city.stability += min(100, round((nation_list[userid].cities[city_name].stability / 20) + 5))

        await nation.save()
        await city.save()
        await tile.save()

structure_types = {
    "temple": StructureType(usable_in=[City], inf_cost=1, resource_cost=["stone"], name="Temple"),
    "grandtemple": StructureType(usable_in=[City], inf_cost=1, resource_cost=["stone"], name="Grand Temple", prereq="Temple"),
    "station": StructureType(usable_in=[City], inf_cost=2, resource_cost=["lumber"], name="Station"),
    "centralstation": StructureType(usable_in=[City], inf_cost=2, resource_cost=["lumber"], name="Central Station", prereq="Station"),
    "district": StructureType(usable_in=[City], inf_cost=1, resource_cost=["lumber", "stone"], name="District"),
    "charcoalpit": StructureType(usable_in=[City], inf_cost=2, resource_cost=["lumber"], name="Charcoal Pit"),
    "smeltery": StructureType(usable_in=[City], inf_cost=2, resource_cost=["stone", "fuel"], name="Smeltery"),
    "port": StructureType(usable_in=[City], inf_cost=2, resource_cost=["stone", "lumber"], name="Port"),
    "foundry": StructureType(usable_in=[City], inf_cost=2, resource_cost=["metal", "fuel"], name="Foundry", tier_req=2)
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

    def __init__(self, linktype: str, origin: City, destination: City, path: list[tuple[int, int]], owner: int, link_id = None):
        self.origin = origin
        self.destination = destination
        self.path = path
        self.owner = owner
        self.linktype = linktype
        self.link_id = link_id
    
    async def save(self):
        await db.save_link(self)

    def build_free(self):
        """
        An alternate form of build that doesn't cost anything, mainly for use in load().
        """
        nation = nation_list[self.owner]
        for location in self.path:
            tile_list[location].structures.append(self.linktype)
            tile_list[location].save()
        nation.links.append(self)

        nation.save()
        self.origin.save()
        self.destination.save()

    def build(self):
        length = len(self.path)
        match self.linktype:
            case "stone":
                inf_cost = math.ceil(length / 2)
                metal_cost = 0
                stone_cost = math.ceil(length / 5)
            case "sea":
                inf_cost = math.ceil(length / 5)
                metal_cost = 0
                stone_cost = 0
            case "simple_rail":
                inf_cost = length
                metal_cost = math.ceil(length / 3)
                stone_cost = 0
            case "quality_rail":
                inf_cost = length * 2
                metal_cost = math.ceil(length / 2)
                stone_cost = 0
        
        nation = nation_list[self.owner]
        econ = nation.econ

        resources = self.origin.inventory + self.destination.inventory
        if resources.count("metal") < metal_cost:
            raise errors.NotEnoughResources("Link construction", ["metal"] * metal_cost, resources)
        if resources.count("stone") < stone_cost:
            raise errors.NotEnoughResources("Link construction", ["stone"] * stone_cost, resources)

        if econ.influence < inf_cost:
            raise errors.NotEnoughEI("Link construction", inf_cost, econ.influence)
        metal_remaining = metal_cost
        last = 0
        while metal_remaining > 0:
            if last == 0:
                if "metal" in self.origin.inventory:
                    self.origin.inventory.remove("metal")
                last = 1
            elif last == 1:
                if "metal" in self.destination.inventory:
                    self.destination.inventory.remove("metal")
                last = 0
            metal_remaining -= 1
            if not ("metal" in self.origin.inventory) and not ("metal" in self.destination.inventory) and metal_remaining > 0:
                raise errors.NotEnoughResources("Link construction", ["metal"] * metal_cost, resources)
        
        stone_remaining = stone_cost
        last = 0
        while stone_remaining > 0:
            if last == 0:
                if "stone" in self.origin.inventory:
                    self.origin.inventory.remove("stone")
                last = 1
            elif last == 1:
                if "stone" in self.destination.inventory:
                    self.destination.inventory.remove("stone")
                last = 0
            stone_remaining -= 1
            if not ("stone" in self.origin.inventory) and not ("stone" in self.destination.inventory) and stone_remaining > 0:
                raise errors.NotEnoughResources("Link construction", ["stone"] * stone_cost, resources)

        econ.influence -= inf_cost

        for location in self.path:
            tile_list[location].structures.append(self.linktype)
            tile_list[location].save()
        nation.links.append(self)

        nation.save()
        econ.save()
        self.origin.save()
        self.destination.save()

async def tick():
    logger.info("Processing game tick...")
    for nation in nation_list.values():
        logger.debug(f"Processing tick for {nation.name}")
        for city in nation.cities.values():
            city.tier = city.calculate_tier()

            await city.save()
        
        nation.econ.influence_cap = nation.econ.calculate_cap()
        nation.econ.influence = nation.econ.influence_cap
        
        await nation.save()
        await nation.econ.save()
        logger.debug(f"Tick for {nation.name} complete")
    
    update_season()
    logger.info("Game tick complete.")

async def load_terrain():
    """
    Loads terrain data from tiles.json into the tiles singleton.
    """
    try:
        logger.info("Starting terrain load...")
        with open("data/tiles.json", "r") as f:
            terrain_data = json.load(f)
        
        for location, tile_info in terrain_data.items():
            stripped_data = location.strip("()").split(", ")
            location = (int(stripped_data[0]), int(stripped_data[1]))
            terrain = tile_info['terrain']

            tile = Tile(terrain, location)
            tile_list[location] = tile
            await tile.save()

        logger.info("Terrain load complete")
        logger.debug(f"[{tile_list}]")
    except Exception as e:
        logger.error(f"Failed to load terrain data: {e}")
        raise

async def load():
    """
    Reloads all game state data and reinstantiates from the database. Use will instantly clear any runtime data not protected by a save.
    """
    logger.warning("Clearing nation data")
    nation_list.clear()
    units.clear()
    
    if not json_terrain:
        tile_list.clear()
    
    logger.info("Starting game data load...")
    nations_data = await db.load_nations_rows()
    for row in nations_data:
        nation = Nation(
            name=row["name"],
            userid=row["id"],
            dossier=json.loads(row["dossier"]),
            color=Color(row["color"])
        )
        nation_list[row["id"]] = nation

    economies_data = await db.load_economies_rows()
    for row in economies_data:
        econ = Econ(
            nationid=row["nationid"],
            influence=row["influence"],
            influence_cap=row["influence_cap"],
        )
        nation_list[row["nationid"]].econ = econ

    if not json_terrain:
        tiles_data = await db.load_tiles_rows()
    else:
        tiles_data = {}
    for row in tiles_data:
        Tile(
            terrain=row["terrain"],
            location=(row["x"], row["y"]),
            owner=row["owner"],
            owned=row["owned"],
            structures=json.loads(row["structures"]) if row["structures"] else [],
        )

    cities_data = await db.load_cities_rows()
    for row in cities_data:
        nation_list[row["owner"]].cities[row["name"]] = City(
            terrain=tile_list[(row["x"], row["y"])].terrain,
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
        unit = Unit(
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
        units.append(unit)
        nation_list[row["owner"]].military[row["name"]] = unit

    links_data = await db.load_links_rows()
    for row in links_data:
        origin = None
        destination = None
        for tile in tile_list:
            if isinstance(tile, City):
                if tile.name == row["origin"]:
                    origin = tile
                elif tile.name == row["destination"]:
                    destination = tile

        link = Link(
            linktype=row["linktype"],
            origin=origin,
            destination=destination,
            path=json.loads(row["path"]),
            owner=row["owner"],
            link_id=row["id"])
        link.build_free()
    
    logger.info("Loaded game data")
    logger.debug(nation_list)