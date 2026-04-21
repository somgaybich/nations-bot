import math
import logging

logger = logging.getLogger(__name__)

import scripts.errors as errors

from game.constants import admin_mode
from game.military import Unit
from game.nation import Nation
from game.region import Region
from game.economy import Econ
from game.authority import Authority
from game.resources import Resource

from world.map import Tile, hex_distance
from world.structures import (LinkType, StructureType, 
                              Link, Structure, structure_types)
from world.world import nation_list, tile_list, units, structures, links

# TODO: new_link expects origin and destination to be cities, 
# how do we fetch those now ???

async def new_authority(default_name: str, owner: int):
    """
    Creates, but does NOT bind or save the authority; these should be done AFTER selection or generation
    """
    return Authority(owner, default_name)

async def new_link(path: list[Tile], linktype: LinkType, owner: int, 
                   origin: Region, destination: Region) -> Link:
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

async def new_army(name: str, userid: int, region_name: str) -> Unit:
    nation = nation_list[userid]
    region = nation.regions.get(region_name)
    econ = nation.econ

    if region is None:
        raise errors.DoesNotExist("region", "Army creation", region_name)
    if econ.influence < 1 and not admin_mode:
        return errors.NotEnoughInfluence("Army creation", 1, econ.influence)
    
    base_strength = 1
    if "Foundry" in region.structure_types():
        base_strength = 1.3

    if not admin_mode:
        econ.influence -= 1
    new_unit = Unit(name=name, type="army", location=region.location, 
                    strength=base_strength, movement_free=3, owner=userid, 
                    home=region_name)
    nation.military[name] = new_unit
    units.append(new_unit)

    await nation.save()
    await econ.save()
    await new_unit.save()

    return new_unit

async def new_fleet(name: str, userid: int, region_name: str) -> Unit:
    nation = nation_list[userid]
    region = nation.regions.get(region_name)
    econ = nation.econ

    if region is None:
        raise errors.DoesNotExist("region", "Fleet creation", region_name)
    if not "Port" in region.structure_types():
        raise errors.MissingStructure("Fleet creation", "Port")
    if econ.influence < 2 and not admin_mode:
        raise errors.NotEnoughInfluence("Fleet creation", 2, econ.influence)
    
    base_strength = 1
    if "Foundry" in region.structure_types():
        base_strength = 1.3
    if not admin_mode:
        econ.influence -= 2
    new_unit = Unit(name=name, type="fleet", location=region.location, 
                    strength=base_strength, movement_free=6, owner=userid, 
                    home=region_name)
    nation.military[name] = new_unit
    units.append(new_unit)

    await nation.save()
    await econ.save()
    await new_unit.save()

    return new_unit

async def new_region(name: str, location: tuple[int, int], owner: int, 
                     capital: bool = False) -> Region:
    """
    A helper function for making new regions.
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
            for city in nation.regions:
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

    new_region = Region(name=name, location=location, 
                        owner=owner, is_capital=capital)
    nation.regions[name] = new_region

    city_tile.structure = Structure(structure_type=structure_types["outpost"], 
                                    location=location, region=name, 
                                    builder=owner)

    await nation.save()
    await new_region.save()
    await city_tile.save()
    
    return new_region

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
    nation = Nation(
        name=name, 
        userid=userid, 
        econ=econ)
    nation_list[userid] = nation
    
    await nation.save()
    await econ.save()
    return nation

async def new_structure(structure_type: StructureType, 
                        location: tuple[int, int], region_name: str, 
                        builder: int) -> Structure:
    nation = nation_list[builder]
    econ = nation.econ
    tile = tile_list[location]
    region = nation.regions[region_name]
    root_tile = tile_list[region.location]
    region_structures = region.structures()

    if len(region_structures) >= 2 and not region.tier >= 2:
        raise errors.TooManyStructures(f"{structure_type.fname} creation", 2)
    if len(region_structures) >= 3 and not region.tier == 4:
        raise errors.TooManyStructures(f"{structure_type.fname} creation", 3)
    
    if tile.structure is not None:
        raise errors.TIleAlreadyHadStructure("Structure creation", location)

    if (structure_type.resource_cost not in region.inventory 
        and not admin_mode):
        raise errors.NotEnoughResources(f"{structure_type.fname} creation", 
                                        structure_type.resource_cost, 
                                        region.inventory)
    if nation.econ.influence < structure_type.inf_cost and not admin_mode:
        raise errors.NotEnoughInfluence(f"{structure_type.fname} creation", 
                                        structure_type.inf_cost, 
                                        econ.influence)
    
    if tile not in region.tiles:
        raise errors.InvalidLocation(f"{structure_type.fname} creation", 
                                     "outide the region")
    
    if "arable" in structure_type.usable_in:
        if not tile.is_arable():
            raise errors.InvalidLocation(f"{structure_type.fname} creation", 
                                         "in a non-arable tile")
    if "coastal" in structure_type.usable_in:
        if not tile.is_coastal():
            raise errors.InvalidLocation(f"{structure_type.fname} creation", 
                                         "in a non-coastal tile")
    if "non-mountain" in structure_type.usable_in:
        if tile.terrain.biome in ["high_mountains", "mountains"]:
            raise errors.InvalidLocation(f"{structure_type.fname} creation", 
                                         "in a mountainous tile")
    if "mountain" in structure_type.usable_in:
        if not tile.terrain.biome in ["high_mountains", "mountains"]:
            raise errors.InvalidLocation(f"{structure_type.fname} creation", 
                                         "in a non-mountainous tile")
        
    if not structure_type.tier_req == 0 and not admin_mode:
        if region.tier < structure_type.tier_req:
            raise errors.RegionTierTooLow(f"{structure_type.fname} creation", 
                                        region.tier, structure_type.tier_req)

    if not admin_mode and hex_distance(root_tile, tile) >= 6:
            raise errors.InvalidLocation("Structure creation", 
                                         "too far from the root settlement")

    if structure_type.prereq != '':
        for region in nation.regions.values():
            if structure_type.fname in region.structure_types():
                raise errors.TooManyUniqueStructures(structure_type.fname)

        # This check must always be last because it has behavior attached!
        if structure_type.prereq in region_structures:
            for structure in structures:
                if not structure.region == region:
                    continue
                if not structure.structure_type.fname == structure_type.prereq:
                    continue

                target_tile = tile_list[structure.location]
                target_tile.structure = None
                await target_tile.save()
                break
            else:
                raise errors.MissingStructure(f"{structure_type.fname} creation", 
                                              structure_type.prereq)
        else:
            raise errors.MissingStructure(f"{structure_type.fname} creation", 
                                          structure_type.prereq)

    items_consumed: list[Resource] = []
    if not admin_mode:
        for item_name in structure_type.resource_cost:
            cost_item = region.find_resource(item_name)
            if cost_item is not None:
                items_consumed.append(cost_item)
        econ.influence -= structure_type.inf_cost

    new_structure = Structure(structure_type, location, region_name, builder)
    tile.structure = new_structure

    if structure_type.resource_prod != '':
        new_resource = Resource(
            name=structure_type.resource_prod,
            origin=location,
            located_at=region_name,
        )
        region.inventory.append(new_resource)

    for item in items_consumed:
        item.used_in = new_structure

    if "Temple" in structure_type.fname:
        current_stability = nation_list[builder].regions[region_name].stability
        region.stability += min(100, round((current_stability / 20) + 5))

    await nation.save()
    await econ.save()
    await region.save()
    await tile.save()

    return new_structure

def trim_path_to_city(path: list[Link], city: Region):
    """
    Removes links so that the path ends at `city`.
    Assumes the path is already valid up to that city.
    """
    removed_links = []
    for i, link in enumerate(path):
        if link.origin == city:
            # city is the start of this link → keep everything before it
            removed_links = path[i:]
            del path[i:]
            break
        if link.destination == city:
            # city is the end of this link → keep through this link
            removed_links = path[i+1:]
            del path[i+1:]
            break
    else:
        path_name = [(link.origin, link.destination) for link in path]
        raise ValueError(f"City '{city.name}' not found in path {path_name}")
    
    for link in removed_links:
        link.transferred -= 1

async def transfer_resource(origin_name: str, origin_owner: int,
                            destination_name: str, destination_owner: int,
                            resource_name: str):
    """
    Safely moves a resource from one city to another. Keep in mind there must be a direct link between the two cities; pathfinding is not tried.
    
    :param origin_name: The name of the origin city.
    :type origin_name: str
    :param origin_owner: The id of the origin city's nation.
    :type origin_owner: int
    :param destination_name: The name of the destination city.
    :type destination_name: str
    :param destination_owner: The id of the destination city's nation.
    :type destination_owner: int
    :param resource_name: The name of the resource to be transferred.
    :type resource_name: str
    """
    origin_nation = nation_list[origin_owner]
    origin_city = origin_nation.regions[origin_name]
    destination_nation = nation_list[destination_owner]
    destination_city = destination_nation.regions[destination_name]

    resource = origin_city.find_resource(resource_name)
    if resource is None:
        raise errors.NotEnoughResources(f"{resource_name} transfer",
                                        [resource_name],
                                        [])
    if resource.used_in is not None:
        raise errors.ResourcesDeployed(f"{resource_name} transfer", 
                                       resource_name)

    transfer_link = links.find(origin_name, destination_name)
    if transfer_link is None:
        raise errors.MissingStructure(f"{resource} transfer", "link")

    visited_cities: set = set()
    for link in resource.path:
        visited_cities.add(link.origin)
        visited_cities.add(link.destination)
        
    if destination_city in visited_cities:
        trim_path_to_city(resource.path, destination_city)
    else:
        capacity = transfer_link.linktype.tier - transfer_link.transferred
        if "Port" in origin_city.structure_types():
            capacity += 1
        if "Port" in destination_city.structure_types():
            capacity += 1

        origin_auth = origin_nation.authorities[origin_city.authority].authtype
        dest_auth = destination_nation.authorities[destination_city.authority].authtype
        if origin_auth == "industrial":
            capacity -= 1
        elif dest_auth == "industrial":
            capacity -= 1
            
        if capacity < 1:
            raise errors.LinkOverburdened(f"{resource} transfer", 
                                          transfer_link)
        resource.path.append(transfer_link)
        transfer_link.transferred += 1

    origin_city.inventory.remove(resource)
    destination_city.inventory.append(resource)
