import json
import logging
from discord import Color

import scripts.database as db

from game.military import Unit
from game.constants import json_terrain

from world.map import Tile, Terrain
from world.structures import Link
from world.cities import City
from world.nation import Nation
from world.economy import Econ
from world.world import tile_list, nation_list, units

logger = logging.getLogger(__name__)

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
            terrain=Terrain(*json.loads(row["terrain"])),
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
            movement_free=row["movement_free"],
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
