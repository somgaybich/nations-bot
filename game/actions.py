import math
import logging

logger = logging.getLogger(__name__)

import scripts.errors as errors

from game.constants import admin_mode
from game.military import Unit
from game.nation import Nation
from game.economy import Econ
from game.authority import Authority
from game.resources import Resource

from world.map import Tile, hex_distance
from world.structures import (LinkType, StructureType, Link, 
                              Structure, City)
from world.world import nation_list, tile_list, units, structures

# TODO: new_link expects origin and destination to be cities, 
# how do we fetch those now ???

async def new_authority(default_name: str, owner: int):
    """
    Creates, but does NOT bind or save the authority; these should be done AFTER selection or generation
    """
    return Authority(owner, default_name)

async def new_link(path: list[Tile], linktype: LinkType, owner: int, 
                   origin: City, destination: City) -> Link:
    length = len(path)
    inf_cost = math.ceil(linktype.inf_cost * length)
    stone_cost = math.ceil(linktype.resource_cost["stone"] * length)
    metal_cost = math.ceil(linktype.resource_cost["metal"] * length)
    
    nation = nation_list[owner]
    econ = nation.econ

    for path_tile in path:
        if linktype.oceanic and not path_tile.terrain.is_water:
            raise errors.InvalidLocation("Link constuction", "in land tiles")
        if not linktype.oceanic and not path_tile.terrain.is_land:
            raise errors.InvalidLocation("Link construction", "in water tiles")

    combined_inventories = origin.inventory + destination.inventory
    resources = [item.name for item in combined_inventories]
    if resources.count("metal") < metal_cost and not admin_mode:
        raise errors.NotEnoughResources("Link construction", 
                                        ["metal"] * metal_cost, resources)
    if resources.count("stone") < stone_cost and not admin_mode:
        raise errors.NotEnoughResources("Link construction", 
                                        ["stone"] * stone_cost, resources)
    if econ.influence < inf_cost and not admin_mode:
        raise errors.NotEnoughInfluence("Link construction", 
                                        inf_cost, econ.influence)
    
    items_consumed: list[Resource] = []
    if not admin_mode:
        metal_remaining = metal_cost
        last = 0
        while metal_remaining > 0:
            if last == 0:
                stone = origin.find_resource("metal")
                if stone is not None:
                    items_consumed.append(stone)
                last = 1
            elif last == 1:
                stone = destination.find_resource("metal")
                if stone is not None:
                    items_consumed.append(stone)
                last = 0
            metal_remaining -= 1
        
        stone_remaining = stone_cost
        last = 0
        while stone_remaining > 0:
            if last == 0:
                stone = origin.find_resource("stone")
                if stone is not None:
                    items_consumed.append(stone)
                last = 1
            elif last == 1:
                stone = destination.find_resource("stone")
                if stone is not None:
                    items_consumed.append(stone)
                last = 0
            stone_remaining -= 1

        econ.influence -= inf_cost

    for path_tile in path:
        if hex_distance(path_tile, origin) <= hex_distance(path_tile, 
                                                           destination):
            root_city = origin
        else:
            root_city = destination
        
        path_tile.link_structures = Structure(linktype, path_tile, 
                                              root_city, owner)
        await path_tile.save()

    new_link = Link(linktype, origin, destination, path, owner)
    nation.links.append(new_link)

    for item in items_consumed:
        item.used_in = new_link

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
    if econ.influence < 1 and not admin_mode:
        return errors.NotEnoughInfluence("Army creation", 1, econ.influence)
    
    base_strength = 1
    if "Foundry" in city.structure_types():
        base_strength = 1.3

    if not admin_mode:
        econ.influence -= 1
    new_unit = Unit(name=name, type="army", location=city.location, 
                    strength=base_strength, movement_free=3, owner=userid, 
                    home=city_name)
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
    if not "Port" in city.structure_types():
        raise errors.MissingStructure("Fleet creation", "Port")
    if econ.influence < 2 and not admin_mode:
        raise errors.NotEnoughInfluence("Fleet creation", 2, econ.influence)
    
    base_strength = 1
    if "Foundry" in city.structure_types():
        base_strength = 1.3
    if not admin_mode:
        econ.influence -= 2
    new_unit = Unit(name=name, type="fleet", location=city.location, 
                    strength=base_strength, movement_free=6, owner=userid, 
                    home=city_name)
    nation.military[name] = new_unit
    units.append(new_unit)

    await nation.save()
    await econ.save()
    await new_unit.save()

    return new_unit

async def new_city(name: str, location: tuple[int, int], owner: int, 
                   capital: bool = False) -> City:
    """
    A helper function for making new cities.
    """
    nation = nation_list[owner]
    city_tile = tile_list[location]

    if city_tile.structure is not None:
        raise errors.TIleAlreadyHadStructure("Settlement creation", location)

    if not city_tile.terrain.is_land:
        raise errors.InvalidLocation("Settlement creation", 
                                     "in ocean tiles")
    elif city_tile.terrain.biome == "high_mountains":
        raise errors.InvalidLocation("Settlement creation", 
                                     "in high mountains")
    
    to_be_claimed = []
    for tile in city_tile.area():
        if tile.location == location:
            continue
        if tile.owner == None:
            to_be_claimed.append(tile.location)
        elif tile.owner == owner:
            continue
        else:
            # Tile is owned by another player
            raise errors.NotOwned('Settlement creation', tile.location)

    if not capital and not admin_mode:
        in_range = False
        for unit in units:
            if hex_distance(unit.location, city_tile) <= 1:
                in_range = True
                break
        if not in_range:
            for city in nation.cities:
                if hex_distance(city, city_tile) <= 6:
                    in_range = True
        if not in_range:
            raise errors.InvalidLocation("Settlement creation", 
                                         "too far from settlements or units")
        
        if nation.econ.influence < 4:
            raise errors.NotEnoughInfluence('Settlement creation', 4, 
                                            nation.econ.influence)
        
    nation.econ.influence -= 4

    for claim_location in to_be_claimed:
        tile_list[claim_location].owner = owner
        await tile_list[claim_location].save()

    new_city = City(terrain=city_tile.terrain, name=name, 
                    location=location, owner=owner)
    nation.cities[name] = new_city
    nation.authorities[nation.name].cities.append(new_city.name)

    city_tile.structure = new_city

    await nation.save()
    await new_city.save()
    await city_tile.save()
    
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
    gov_authority = Authority(nationid=userid, name=name, authtype="government", cap=3)
    nation = Nation(
        name=name, 
        userid=userid, 
        econ=econ,
        authorities={
            name: gov_authority
        })
    nation_list[userid] = nation
    
    await nation.save()
    await econ.save()
    return nation

async def new_structure(structure_type: StructureType, 
                        location: tuple[int, int], city_name: str, 
                        builder: int) -> Structure:
    nation = nation_list[builder]
    econ = nation.econ
    tile = tile_list[location]
    root_city = nation.cities[city_name]
    root_tile = tile_list[root_city.location]
    city_structures = root_city.structures()

    if len(city_structures) >= 2 and not root_city.tier >= 2:
        raise errors.TooManyStructures(f"{structure_type.name} creation", 2)
    if len(city_structures) >= 3 and not root_city.tier == 4:
        raise errors.TooManyStructures(f"{structure_type.name} creation", 3)
    
    if tile.structure is not None:
        raise errors.TIleAlreadyHadStructure("Settlement creation", location)

    if (structure_type.resource_cost not in root_city.inventory 
        and not admin_mode):
        raise errors.NotEnoughResources(f"{structure_type.name} creation", 
                                        structure_type.resource_cost, 
                                        root_city.inventory)
    if nation.econ.influence < structure_type.inf_cost and not admin_mode:
        raise errors.NotEnoughInfluence(f"{structure_type.name} creation", 
                                        structure_type.inf_cost, 
                                        econ.influence)
    
    if tile not in root_city.developed_area():
        raise errors.InvalidLocation(f"{structure_type.name} creation", 
                                     "outide the settlement's range")
    
    if "arable" in structure_type.usable_in:
        if not tile.is_arable():
            raise errors.InvalidLocation(f"{structure_type.name} creation", 
                                         "in a non-arable tile")
    if "coastal" in structure_type.usable_in:
        if not tile.is_coastal():
            raise errors.InvalidLocation(f"{structure_type.name} creation", 
                                         "in a non-coastal tile")
    if "non-mountain" in structure_type.usable_in:
        if tile.terrain.biome in ["high_mountains", "mountains"]:
            raise errors.InvalidLocation(f"{structure_type.name} creation", 
                                         "in a mountainous tile")
    if "mountain" in structure_type.usable_in:
        if not tile.terrain.biome in ["high_mountains", "mountains"]:
            raise errors.InvalidLocation(f"{structure_type.name} creation", 
                                         "in a non-mountainous tile")
        
    if not structure_type.tier_req == 0 and not admin_mode:
        if root_city.tier < structure_type.tier_req:
            raise errors.CityTierTooLow(f"{structure_type.name} creation", 
                                        tile.tier, structure_type.tier_req)

    if not admin_mode and hex_distance(root_tile, tile) >= 6:
            raise errors.InvalidLocation("Settlement creation", 
                                         "too far from the root settlement")

    if structure_type.prereq != '':
        for city in nation.cities.values():
            if structure_type.name in city.structure_types():
                raise errors.TooManyUniqueStructures(structure_type.name)

        # This check must always be last because it has behavior attached!
        if structure_type.prereq in city_structures:
            for structure in structures:
                if not structure.root_city == root_city:
                    continue
                if not structure.structure_type.name == structure_type.prereq:
                    continue

                target_tile = tile_list[structure.location]
                target_tile.structure = None
                await target_tile.save()
                break
            else:
                raise errors.MissingStructure(f"{structure_type.name} creation", 
                                              structure_type.prereq)
        else:
            raise errors.MissingStructure(f"{structure_type.name} creation", 
                                          structure_type.prereq)

    items_consumed: list[Resource] = []
    if not admin_mode:
        for item_name in structure_type.resource_cost:
            cost_item = root_city.find_resource(item_name)
            if cost_item is not None:
                items_consumed.append(cost_item)
        econ.influence -= structure_type.inf_cost

    new_structure = Structure(structure_type, location, city_name, builder)
    tile.structure = new_structure

    if structure_type.resource_prod != '':
        new_resource = Resource(
            name=structure_type.resource_prod,
            origin=location,
            located_at=city_name,
        )
        root_city.inventory.append(new_resource)

    for item in items_consumed:
        item.used_in = new_structure

    if "Temple" in structure_type.name:
        current_stability = nation_list[builder].cities[city_name].stability
        root_city.stability += min(100, round((current_stability / 20) + 5))

    await nation.save()
    await econ.save()
    await root_city.save()
    await tile.save()

    return new_structure