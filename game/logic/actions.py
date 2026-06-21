import logging
from typing import TYPE_CHECKING

logger = logging.getLogger(__name__)

import scripts.errors as errors

from data.constants import admin_mode
from game.objs.market import Market
from game.objs.military import Unit
from game.objs.nation import Nation
from game.objs.region import Region
from game.objs.economy import Econ
from game.objs.industry import industry_types

from game.objs.map import hex_distance
from game.objs.structures import StructureType, Structure, structure_types

if TYPE_CHECKING:
    from world.world import GameState

async def new_army(
        name: str, 
        owner: int, 
        region_name: str,
        state: "GameState"
    ) -> Unit:
    """
    Creates a new army in a specified city.

    :param name: The name of the unit.
    :param owner: The NID of the nation that owns the unit.
    :param region_name: The region/city to train the unit in. 
    :type name: str
    :type owner: int
    :type region_name: str
    """
    nation = state.nations[owner]
    region_id = state.region_ids[region_name]
    region = state.regions[region_id]
    econ = nation.econ

    if region is None:
        raise errors.DoesNotExist("region", "Army creation", region_name)
    if econ.influence < 1 and not admin_mode:
        return errors.NotEnoughInfluence("Army creation", 1, econ.influence)

    current_units = []
    for unit_id in nation.units:
        unit = state.units[unit_id]
        if unit.home != region_id:
            continue
        
        current_units.append(unit)
        if unit.status == "TRAINING":
            raise errors.AlreadyTraining()

    region_unit_cap = region.city_tier + 1
    if len(current_units) >= region_unit_cap:
        raise errors.TooManyUnits()

    base_strength = 1
    # FIXME: Modify base strength based on logistics

    if not admin_mode:
        econ.influence -= 1
    new_unit = Unit(name=name, type="army", location=region.location, 
                    strength=base_strength, movement_free=3, owner=owner, 
                    home=region_id, status="TRAINING")

    await new_unit.save()
    state.units[new_unit.id] = new_unit
    state.unit_ids[name] = new_unit.id
    nation.units.append(new_unit.id)
    await nation.save()
    await econ.save()

    return new_unit

async def new_fleet(
        name: str, 
        userid: int, 
        region_name: str,
        state: "GameState"
    ) -> Unit:
    """
    Creates a new fleet in a specified city.

    :param name: The name of the new fleet.
    :param userid: The NID of the nation that will own the fleet.
    :param region_name: The city/region to create the fleet in.
    :type name: str
    :type userid: int
    :type region_name: str
    """
    nation = state.nations[userid]
    region_id = state.region_ids[region_name]
    region = state.regions[region_id]
    econ = nation.econ

    if region is None:
        raise errors.DoesNotExist("region", "Fleet creation", region_name)
    if not "Port" in region.structure_types():
        raise errors.MissingStructure("Fleet creation", "Port")
    if econ.influence < 2 and not admin_mode:
        raise errors.NotEnoughInfluence("Fleet creation", 2, econ.influence)
    
    current_units = []
    for unit_id in nation.units:
        unit = state.units[unit_id]
        if unit.home != region_id:
            continue

        current_units.append(unit)
        if unit.status == "TRAINING":
            raise errors.AlreadyTraining()

    region_unit_cap = region.city_tier + 1
    if len(current_units) >= region_unit_cap:
        raise errors.TooManyUnits()

    base_strength = 1
    # FIXME: Modify base strength based on logistics

    if not admin_mode:
        econ.influence -= 2
    new_unit = Unit(name=name, type="fleet", location=region.location, 
                    strength=base_strength, movement_free=6, owner=userid, 
                    home=region_id)
    
    await new_unit.save()
    state.units[new_unit.id] = new_unit
    state.unit_ids[name] = new_unit.id
    nation.units.append(new_unit.id)
    await nation.save()
    await econ.save()

    return new_unit

async def new_region(
        name: str, 
        location: tuple[int, int], 
        owner: int, 
        state: "GameState",
        capital: bool = False
    ) -> Region:
    """
    Makes a new region at a specified location.

    :param name: The name of the new city/region.
    :param location: The location to put the new center city.
    :param owner: The NID of the nation that will own the region.
    :param capital: Whether this region is the nation's capital.
    :type name: str
    :type location: tuple[int, int]
    :type owner: int
    :type capital: bool
    """
    nation = state.nations[owner]
    city_tile = state.tiles[location]

    for nation_region in state.regions.values():
        if nation_region.name == name:
            raise errors.NameInUse(name, "city")

    if city_tile.structure is not None:
        raise errors.TIleAlreadyHadStructure("Settlement creation", location)

    if not city_tile.terrain.is_land:
        raise errors.InvalidLocation("Settlement creation", 
                                     "in ocean tiles")
    elif city_tile.terrain.biome == "high_mountains":
        raise errors.InvalidLocation("Settlement creation", 
                                     "in high mountains")
    
    to_be_claimed = []
    for tile in city_tile.area(state):
        if tile.location == location:
            continue
        if tile.owner == None:
            to_be_claimed.append(tile.location)
        elif state.regions[tile.owner].owner == owner:
            continue
        else:
            # Tile is owned by another player
            raise errors.NotOwned('Settlement creation', tile.location)

    if not capital and not admin_mode:
        in_range = False
        for unit in state.units.values():
            if hex_distance(unit.location, city_tile) <= 1:
                in_range = True
                break
        if not in_range:
            for region_id in nation.regions:
                nation_region = state.regions[region_id]
                region_city = nation_region.location
                if hex_distance(region_city, city_tile) <= 6:
                    in_range = True
        if not in_range:
            raise errors.InvalidLocation("Settlement creation", 
                                         "too far from settlements or units")
        
        if nation.econ.influence < 4:
            raise errors.NotEnoughInfluence('Settlement creation', 4, 
                                            nation.econ.influence)
        
        nation.econ.influence -= 4

    new_region = Region(name=name, location=location, 
                        owner=owner, is_capital=capital, state=state)
    
    await new_region.save()
    state.regions[new_region.id] = new_region
    state.region_ids[name] = new_region.id
    nation.regions.append(new_region.id)

    for claim_location in to_be_claimed:
        state.tiles[claim_location].owner = new_region.id
        await state.tiles[claim_location].save()

    new_market = Market(name=name, owner=owner, regions=[new_region])
    state.markets[name] = new_market
    await new_industry("subsistence", name, state)

    city_tile.structure = Structure(structure_type=structure_types["outpost"], 
                                    location=location, region=name, 
                                    owner=owner)

    await nation.save()
    await new_region.save()
    await city_tile.save()

    return new_region

async def new_nation(
        name: str, 
        userid: int, 
        state: "GameState"
    ) -> Nation:
    """
    Creates a new nation.

    :param name: The name of the new nation.
    :param userid: The NID to assign the nation.
    :type name: str
    :type userid: int
    """
    for existing_nation in state.nations.values():
        if existing_nation.name == name:
            raise errors.NameInUse(name, "nation")
        elif existing_nation.userid == userid:
            raise errors.UserHasNation(userid)
    
    econ = Econ(userid)
    nation = Nation(
        name=name, 
        userid=userid, 
        econ=econ)
    state.nations[userid] = nation
    
    await nation.save()
    await econ.save()
    return nation

async def new_structure(
        structure_type: StructureType, 
        location: tuple[int, int], 
        region_name: str, 
        owner: int,
        state: "GameState"
    ) -> Structure:
    """
    Creates a new structure of a specified type in a specified tile.
    
    :param structure_type: The StructureType to give the structure.
    :param location: The tile to put the structure in.
    :param region_name: The region the structure will belong to. (Might be unnecessary?)
    :param owner: The NID of the nation that will own the structure.
    :type structure_type: StructureType
    :type location: tuple[int, int]
    :type region_name: str
    :type owner: int
    """
    nation = state.nations[owner]
    econ = nation.econ
    tile = state.tiles[location]
    region_id = state.region_ids[region_name]
    region = state.regions[region_id]
    root_tile = state.tiles[region.location]
    region_structures = region.structures(state)

    if len(region_structures) >= 2 and not region.city_tier >= 2:
        raise errors.TooManyStructures(f"{structure_type.fname} creation", 2)
    if len(region_structures) >= 3 and not region.city_tier == 4:
        raise errors.TooManyStructures(f"{structure_type.fname} creation", 3)
    
    if tile.structure is not None:
        raise errors.TIleAlreadyHadStructure("Structure creation", location)
    
    if tile not in region.tiles:
        raise errors.InvalidLocation(f"{structure_type.fname} creation", 
                                     "outide the region")

    if not admin_mode and hex_distance(root_tile, tile) >= 6:
            raise errors.InvalidLocation("Structure creation", 
                                         "too far from the root settlement")

    if not admin_mode:
        econ.influence -= structure_type.inf_cost

    new_structure = Structure(structure_type, location, region.id, owner)
    tile.structure = new_structure

    await nation.save()
    await econ.save()
    await region.save()
    await tile.save()

    return new_structure

async def new_industry(
        industry_name: str, 
        region_name: str, 
        state: "GameState"
    ):
    """
    Creates a new industry of the specified type in the specified region.

    :param industry_name: The name of the industry type to create. See 
    :class:`game.objs.industry.industry_types` for valid values.
    :param region_name: The name of the region to create the industry in.
    :type industry_name: str
    :type region_name: str
    """
    industry_type = industry_types[industry_name]
    region_id = state.region_ids[region_name]
    region = state.regions[region_id]
    nation = state.nations[region.owner]
    
    if nation.econ.influence < industry_type.cost:
        raise errors.NotEnoughInfluence(
            action="Industry creation",
            required=industry_type.cost,
            had=nation.econ.influence)

    nation.econ.influence -= industry_type.cost
    region.industries.append(industry_name)
    
    await region.save()
    await nation.save()