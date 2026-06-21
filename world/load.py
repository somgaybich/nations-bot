import json
import logging
from discord import Color
from typing import TYPE_CHECKING

import world.database as db

from game.objs.military import Unit
from game.objs.nation import Nation
from game.objs.region import Region
from game.objs.economy import Econ
from game.objs.market import build_markets

from game.objs.map import Tile, Terrain
from game.objs.structures import Structure, structure_types

if TYPE_CHECKING:
    from world.world import GameState

logger = logging.getLogger(__name__)

async def load(state: "GameState", map_only: bool = False):
    """
    Reloads all game state data and reinstantiates from the database. Use will instantly clear any runtime data not protected by a save.

    :param map_only: Whether to only load the tile data from the database. Will ignore all other game data.
    :type map_only: bool
    """
    logger.warning("Clearing nation data")
    state.nations.clear()
    state.units.clear()
    
    logger.info("Starting game data load...")
    tiles_data = await db.load_tiles_rows()
    for row in tiles_data:
        tile = Tile(
            terrain=Terrain(*json.loads(row["terrain"])),
            location=(row["x"], row["y"]),
            owner=row["owner"]
        )
        state.tiles[tile.location] = tile

        if row["structure"] != "{}":
            structure_data = json.loads(row["structure"])
            structure = Structure(
                structure_type=structure_types[structure_data['structure_type']],
                location=(structure_data['x'], structure_data['y']),
                region=structure_data['region'],
                owner=structure_data['builder']
            )
            tile.structure = structure

    if map_only:
        logger.info("Loaded map data")
        return

    nations_data = await db.load_nations_rows()
    for row in nations_data:
        nation = Nation(
            name=row["name"],
            userid=row["id"],
            dossier=json.loads(row["dossier"]),
            color=Color(row["color"])
        )
        state.nations[row["id"]] = nation

    region_data = await db.load_regions_rows()
    for row in region_data:
        region = Region(
            name=row["name"],
            location=(row["x"], row["y"]),
            city_tier=row["city_tier"],
            owner=row["owner"],
            is_capital=row["capital"],
            tiles=[tuple(tile) for tile in json.loads(row["tiles"])],
            industries=json.loads(row["industries"]),
            id=row["id"],
            state=state
        )

        state.nations[region.owner].regions.append(region.id)
        state.regions[region.id] = region
        state.region_ids[region.name] = region.id

    economies_data = await db.load_economies_rows()
    for row in economies_data:
        econ = Econ(
            nationid=row["nationid"],
            influence=row["influence"],
            influence_cap=row["influence_cap"],
        )
        state.nations[econ.nationid].econ = econ

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
            movement_free=row["movement_free"],
            status=row["status"],
            owner=row["owner"],
            id=row["id"],
        )
        
        state.nations[unit.owner].units.append(unit.id)
        state.units[unit.id] = unit
        state.unit_ids[unit.name] = unit.id

    await build_markets(state)

    logger.info("Loaded game data")
    logger.debug(state)
