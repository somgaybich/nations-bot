import math
import logging

logger = logging.getLogger(__name__)

import scripts.errors as errors

from game.military import Unit

from world.map import Tile, hex_distance
from world.structures import LinkType, StructureType, Link, Structure
from world.cities import City
from game.nation import Nation
from world.world import nation_list, tile_list, units
from game.economy import Econ

async def new_link(path: list[Tile], linktype: LinkType, owner: int, origin: City, destination: City) -> Link:
    length = len(path)
    inf_cost = math.ceil(linktype.inf_cost * length)
    stone_cost = math.ceil(linktype.resource_cost["stone"] * length)
    metal_cost = math.ceil(linktype.resource_cost["metal"] * length)
    
    nation = nation_list[owner]
    econ = nation.econ

    for location in path:
        if linktype.oceanic and not location.terrain.is_water:
            raise errors.InvalidLocation("Link constuction", "in land tiles")
        if not linktype.oceanic and not location.terrain.is_land:
            raise errors.InvalidLocation("Link construction", "in water tiles")

    resources = origin.inventory + destination.inventory
    if resources.count("metal") < metal_cost:
        raise errors.NotEnoughResources("Link construction", ["metal"] * metal_cost, resources)
    if resources.count("stone") < stone_cost:
        raise errors.NotEnoughResources("Link construction", ["stone"] * stone_cost, resources)
    if econ.influence < inf_cost:
        raise errors.NotEnoughInfluence("Link construction", inf_cost, econ.influence)
    
    metal_remaining = metal_cost
    last = 0
    while metal_remaining > 0:
        if last == 0:
            if "metal" in origin.inventory:
                origin.inventory.remove("metal")
            last = 1
        elif last == 1:
            if "metal" in destination.inventory:
                destination.inventory.remove("metal")
            last = 0
        metal_remaining -= 1
        
    stone_remaining = stone_cost
    last = 0
    while stone_remaining > 0:
        if last == 0:
            if "stone" in origin.inventory:
                origin.inventory.remove("stone")
            last = 1
        elif last == 1:
            if "stone" in destination.inventory:
                destination.inventory.remove("stone")
            last = 0
        stone_remaining -= 1

    econ.influence -= inf_cost

    for location in path:
        tile = tile_list[location]
        if hex_distance(tile, origin) <= hex_distance(tile, destination):
            tile.structures.append(Structure(linktype, location, origin, owner))
        else:
            tile.structures.append(Structure(linktype, location, destination, owner))
        tile.save()
    new_link = Link(linktype, origin, destination, path, owner)
    nation.links.append(new_link)

    await nation.save()
    await econ.save()
    await origin.save()
    await destination.save()

    return new_link

async def new_army(name: str, userid: int, city_name: str) -> Unit:
    nation = nation_list[userid]
    city = nation.cities.get(city_name)
    econ = nation.econ

    if city is None:
        raise errors.DoesNotExist("city", "Army creation", city_name)
    if econ.influence < 1:
        return errors.NotEnoughInfluence("Army creation", 1, econ.influence)
    
    base_strength = 1
    if city.structures.has("Foundry"):
        base_strength = 1.3

    econ.influence -= 1
    new_unit = Unit(name=name, type="army", location=city.location, strength=base_strength, movement_free=3)
    nation.military[name] = new_unit
    units.append(new_unit)

    await nation.save()
    await econ.save()
    await new_unit.save()

    return new_unit

async def new_fleet(name: str, userid: int, city_name: str) -> Unit:
    nation = nation_list[userid]
    city = nation.cities.get(city_name)
    econ = nation.econ

    if city is None:
        raise errors.DoesNotExist("city", "Fleet creation", city_name)
    if not city.structures.has("Port"):
        raise errors.MissingStructure("Fleet creation", "Port")
    if econ.influence < 2:
        raise errors.NotEnoughInfluence("Fleet creation", 2, econ.influence)
    
    base_strength = 1
    if city.structures.has("Foundry"):
        base_strength = 1.3
    
    econ.influence -= 2
    new_unit = Unit(name=name, type="fleet", location=city.location, strength=base_strength, movement_free=6)
    nation.military[name] = new_unit
    units.append(new_unit)

    await nation.save()
    await econ.save()
    await new_unit.save()

    return new_unit

async def new_city(name: str, location: tuple[int, int], owner: int) -> City:
    """
    A helper function for making new cities.
    """
    if not tile_list[location].terrain.is_land:
        raise errors.InvalidLocation("Settlement creation", "in ocean tiles")
    elif tile_list[location].terrain.land_biome == "high_mountains":
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
    
    return new_city

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

async def new_structure(structure_type: StructureType, location: tuple[int, int], root_city: str, builder: int) -> Structure:
    nation = nation_list[builder]
    econ = nation.econ
    tile = tile_list[location]
    city = nation.cities[root_city]
    if len(city.structures) == 2 and not city.tier >= 2:
        raise errors.TooManyStructures(f"{structure_type.name} creation", 2)
    if len(city.structures) == 3 and not city.tier == 4:
        raise errors.TooManyStructures(f"{structure_type.name} creation", 3)
    if structure_type.resource_cost not in city.inventory:
        raise errors.NotEnoughResources(f"{structure_type.name} creation", structure_type.resource_cost, city.inventory)
    if nation_list[builder].econ.influence < structure_type.inf_cost:
        raise errors.NotEnoughInfluence(f"{structure_type.name} creation", structure_type.inf_cost, econ.influence)
    if structure_type.usable_in == ["city"]:
        if not isinstance(tile, City):
            raise errors.InvalidLocation(f"{structure_type.name} creation", f"in unsettled tiles")
    elif tile.terrain.land_biome not in structure_type.usable_in:
        raise errors.InvalidLocation(f"{structure_type.name} creation", f"in {tile.terrain.land_biome} tiles")
    if tile not in city.area() and city.tier != 4:
        raise errors.InvalidLocation(f"{structure_type.name} creation", "outide the settlement's range")
    if tile not in city.metroarea() and city.tier == 4:
        raise errors.InvalidLocation(f"{structure_type.name} creation", "outide the settlement's range")
    if not structure_type.tier_req == 0 and location == city.location:
        if tile.tier < structure_type.tier_req:
            raise errors.CityTierTooLow(f"{structure_type.name} creation", tile.tier, structure_type.tier_req)
        
    if structure_type.prereq != '':
        for city in nation.cities.values():
            if city.structures.has(structure_type.name):
                raise errors.TooManyUniqueStructures(structure_type.name)

        # This check must always be last because it has behavior attached!
        for structure in tile.structures:
            index = 0
            if structure.structure_type.name == structure_type.prereq:
                tile.structures.remove(structure)
                break
            else:
                index += 1
                if index == len(tile.structures):
                    raise errors.MissingStructure(structure_type.name + " creation", structure_type.name)

    for item in structure_type.resource_cost:
        city.inventory.remove(item)
    econ.influence -= structure_type.inf_cost

    new_structure = Structure(structure_type, location, root_city, builder)
    tile.structures.append(new_structure)

    if structure_type.name == "Temple" or structure_type.name == "Grand Temple":
        city.popularity += min(100, round((nation_list[builder].cities[root_city].popularity / 10) + 5))
        city.stability += min(100, round((nation_list[builder].cities[root_city].stability / 20) + 5))

    await nation.save()
    await city.save()
    await tile.save()

    return new_structure