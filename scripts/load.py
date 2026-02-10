import json
import logging
import ast
from discord import Color

import scripts.database as db

from game.military import Unit
from game.resources import Resource

from world.map import Tile, Terrain
from world.structures import Link, Structure, City, structure_types
from game.nation import Nation
from game.economy import Econ
from world.world import tile_list, nation_list, units, links

logger = logging.getLogger(__name__)

async def load(map_only: bool = False):
    """
    Reloads all game state data and reinstantiates from the database. Use will instantly clear any runtime data not protected by a save.

    :param map_only: Whether to only load the tile data from the database. Will ignore all other game data.
    """
    logger.warning("Clearing nation data")
    nation_list.clear()
    units.clear()
    
    logger.info("Starting game data load...")
    tiles_data = await db.load_tiles_rows()
    for row in tiles_data:
        structure_data = json.loads(row["structure"])
        structure = None
        if "name" in structure_data:
            decoded_inventory = []
            inventory_data = json.loads(structure_data['inventory'])
            for item_data in inventory_data:
                origin = ast.literal_eval(item_data['origin'])
                encoded_path = ast.literal_eval(item_data['path'])

                decoded_item = Resource(
                    name=item_data['name'],
                    origin=ast.literal_eval(item_data['origin']),
                    located_at=item_data['located_at'],
                    # We keep the path encoded for now
                    # The links don't exist yet to actually bind them
                    path=encoded_path
                )
            structure = City(
                name=structure_data['name'],
                tier=structure_data['tier'],
                location=(structure_data['x'], structure_data['y']),
                owner=structure_data['owner'],
                stability=structure_data['stability'],
                inventory=json.loads(structure_data['inventory']),
                authority=structure_data['authority']
            )
        elif structure_data != {}:
            structure = Structure(
                structure_type=structure_types[structure_data['structure_type']],
                location=json.loads(structure_data['x'], structure_data['y']),
                root_city=structure_data['root_city'],
                builder=structure_data['builder']
            )

        link_structures = []
        if row['link_structures'] is not None:
            link_structures_data = json.loads(row['link_structures'])
            for link_structure in link_structures_data:
                link_structures.append(Structure(
                    structure_type=link_structure['structure_type'],
                    location=(link_structure['x'], link_structure['y']),
                    root_city=link_structure['root_city'],
                    builder=link_structure['builder']
                ))

        tile = Tile(
            terrain=Terrain(*json.loads(row["terrain"])),
            location=(row["x"], row["y"]),
            owner=row["owner"],
            owned=row["owned"],
            structure=structure,
            link_structures=link_structures
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
            link_id=row["id"],
            transferred=row['resources_transferred'])
        
        links.append(link)
        nation_list[link.owner].links.append(link)

        for city in nation_list[link.owner].cities.values():
            for item in city.inventory:
                for encoded_link in item.path:
                    if encoded_link == link.encode():
                        item.path[item.path.index(encoded_link)] = link
                
                for link in item.path:
                    if not isinstance(link, Link):
                        logger.warning(f"{link} was not properly decoded!")

    logger.info("Loaded game data")
    logger.debug(nation_list)
