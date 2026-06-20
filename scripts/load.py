import json
import logging
import ast
from discord import Color

import scripts.database as db

from game.military import Unit
from game.nation import Nation
from game.region import Region
from game.economy import Econ

from world.map import Tile, Terrain
from world.structures import Structure, structure_types
from world.world import tile_list, nation_list, units, structures, regions

logger = logging.getLogger(__name__)

async def load(map_only: bool = False):
    """
    Reloads all game state data and reinstantiates from the database. Use will instantly clear any runtime data not protected by a save.

    :param map_only: Whether to only load the tile data from the database. Will ignore all other game data.
    :type map_only: bool
    """
    logger.warning("Clearing nation data")
    nation_list.clear()
    units.clear()
    
    logger.info("Starting game data load...")
    tiles_data = await db.load_tiles_rows()
    for row in tiles_data:
        structure = None
        if row["structure"] != "{}":
            structure_data = json.loads(row["structure"])
            structure = Structure(
                structure_type=structure_types[structure_data['structure_type']],
                location=(structure_data['x'], structure_data['y']),
                region=structure_data['region'],
                owner=structure_data['builder']
            )
            structures.append(structure)

        tile = Tile(
            terrain=Terrain(*json.loads(row["terrain"])),
            location=(row["x"], row["y"]),
            owner=row["owner"],
            structure=structure
        )
        tile_list[tile.location] = tile

    if map_only:
        logger.info("Loaded map data")
        return

    nations_data = await db.load_nations_rows()
    for row in nations_data:
        nation = Nation(
            name=row["name"],
            userid=row["id"],
            dossier=json.loads(row["dossier"]),
            econ=None,
            color=Color(row["color"])
        )
        nation_list[row["id"]] = nation

    region_data = await db.load_regions_rows()
    for row in region_data:
        region = Region(
            name=row["name"],
            location=(row["x"], row["y"]),
            city_tier=row["city_tier"],
            owner=row["owner"],
            is_capital=row["capital"],
            tiles=[tuple(tile) for tile in json.loads(row["tiles"])],
            market=row["market"],
            industries=json.loads(row["industries"])
        )

        nation_list[row["owner"]].regions.update({
            row["name"]: region
        })
        regions.update({row["name"]: region})

    economies_data = await db.load_economies_rows()
    for row in economies_data:
        econ = Econ(
            nationid=row["nationid"],
            influence=row["influence"],
            influence_cap=row["influence_cap"],
        )
        nation_list[row["nationid"]].econ = econ

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
        units.append(unit)
        nation_list[row["owner"]].military[row["name"]] = unit

    logger.info("Loaded game data")
    logger.debug(nation_list)
