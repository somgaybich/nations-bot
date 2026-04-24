import json
import logging
import ast
from discord import Color

import scripts.database as db

from game.military import Unit
from game.resources import Resource

from world.map import Tile, Terrain
from world.structures import Link, Structure, structure_types
from game.nation import Nation
from game.region import Region
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
        structure = None
        if row["structure"] != "{}":
            structure_data = json.loads(row["structure"])
            structure = Structure(
                structure_type=structure_types[structure_data['structure_type']],
                location=(structure_data['x'], structure_data['y']),
                region=structure_data['region'],
                builder=structure_data['builder']
            )

        link_structures = []
        if row['link_structures'] != "[]":
            link_structures_data = json.loads(row['link_structures'])
            for link_structure in link_structures_data:
                link_structures.append(Structure(
                    structure_type=link_structure['structure_type'],
                    location=(link_structure['x'], link_structure['y']),
                    region=link_structure['region'],
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

    region_data = await db.load_regions_rows()
    for row in region_data:
        decoded_inventory = []
        inventory_data = json.loads(row['inventory'])
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

            decoded_inventory.append(decoded_item)

        region = Region(
            name=row["name"],
            location=(row["x"], row["y"]),
            city_tier=row["tier"],
            owner=row["owner"],
            stability=row["stability"],
            inventory=decoded_inventory,
            authority=row["authority"],
            is_capital=row["capital"],
            tiles=[tuple(tile) for tile in json.loads(row["tiles"])]
        )

        nation_list[row["owner"]].regions.update({
            row["name"]: region
        })

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
            # This check doesn't work, but I'm about to redo all logic involving links anyway so idrc
            if isinstance(tile, Region):
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

        for region in nation_list[link.owner].regions.values():
            for item in region.inventory:
                for encoded_link in item.path:
                    if encoded_link == link.encode():
                        item.path[item.path.index(encoded_link)] = link
                
                for link in item.path:
                    if not isinstance(link, Link):
                        logger.warning(f"{link} was not properly decoded!")

    logger.info("Loaded game data")
    logger.debug(nation_list)
