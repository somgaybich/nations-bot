import aiosqlite
import json
import logging
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from game.objs.nation import Nation
    from game.objs.market import Market
    from game.objs.economy import Econ
    from game.objs.unit import Unit
    from game.objs.region import Region
    from game.objs.map import Tile
    from game.objs.structures import Structure

logger = logging.getLogger(__name__)

_db: Optional[aiosqlite.Connection] = None

async def init_db(file: str = "data/nations.db"):
    """
    Creates a new database connection.
    
    :param file: Path from the root to the database file.
    :type file: str
    """
    logger.info("Starting database connection")
    global _db
    if _db is not None:
        logger.warning("Tried to start database connection when there was already one initialized")
        return
    
    _db = await aiosqlite.connect(file)
    await _db.execute("PRAGMA foreign_keys = ON;")
    _db.row_factory = aiosqlite.Row

    await _db.execute(
    """
    CREATE TABLE IF NOT EXISTS nations (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        dossier TEXT,
        color INTEGER)
    """)
    logger.debug("Created nations table")

    await _db.execute(
    """
    CREATE TABLE IF NOT EXISTS regions (
        name TEXT PRIMARY KEY,
        x INTEGER NOT NULL,
        y INTEGER NOT NULL,
        owner INTEGER NOT NULL,
        tiles TEXT,
        authority TEXT,
        capital TEXT,
        city_tier INTEGER,
        market TEXT,
        industries TEXT)
    """
    )
    logger.debug("Created regions table")

    await _db.execute(
    """
    CREATE TABLE IF NOT EXISTS units (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        type TEXT NOT NULL,
        home TEXT NOT NULL,
        x INTEGER NOT NULL,
        y INTEGER NOT NULL,
        strength INTEGER NOT NULL,
        morale INTEGER NOT NULL,
        exp INTEGER NOT NULL,
        movement_free INTEGER NOT NULL,
        status TEXT NOT NULL,
        owner INTEGER NOT NULL)
    """)
    logger.debug("Created units table")

    await _db.execute(
    """
    CREATE TABLE IF NOT EXISTS tiles (
        x INTEGER NOT NULL,
        y INTEGER NOT NULL,
        terrain TEXT NOT NULL,
        owner TEXT,
        structure TEXT,
        link_structures TEXT,
        PRIMARY KEY (x, y))
    """)
    logger.debug("Created tiles table")
        
    await _db.execute(
        """
        CREATE TABLE IF NOT EXISTS economies (
            nationid INTEGER PRIMARY KEY,
            influence INTEGER NOT NULL,
            influence_cap INTEGER NOT NULL)
        """)
    logger.debug("Created economies table")

    await _db.execute(
        """
        CREATE TABLE IF NOT EXISTS markets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            owner INTEGER NOT NULL,
            regions TEXT NOT NULL)
        """)
    logger.debug("Created markets table")

    await _db.commit()
    logger.info("Database started")

async def close_db():
    global _db
    if _db is not None:
        await _db.close()
        _db = None

def get_db() -> aiosqlite.Connection:
    if _db is None:
        raise RuntimeError("Database not initialized")
    return _db

# ---------------

async def save_nation(nation: "Nation"):
    logger.debug(f"Saving nation at {nation.userid}")
    await get_db().execute(
        """
        INSERT INTO nations (id, name, dossier, color)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            name = excluded.name,
            dossier = excluded.dossier,
            color = excluded.color
        """,
        (nation.userid, nation.name, json.dumps(nation.dossier), int(nation.color))
    )

async def load_nations_rows():
    async with get_db().execute("SELECT * FROM nations") as cursor:
        return await cursor.fetchall()

# ---------------

async def save_region(region: "Region"):
    logger.debug(f"Saving region at {region.name}")
    await get_db().execute(
        """
        INSERT INTO regions (
            name, x, y, owner, tiles, capital, city_tier, market, industries
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(name) DO UPDATE SET
            name = excluded.name,
            tiles = excluded.tiles,
            city_tier = excluded.city_tier,
            market = excluded.market,
            industries = excluded.industries
        """,
        (region.name, region.location[0], region.location[1], region.owner, 
         json.dumps(region.tiles), json.dumps(region.is_capital), 
         region.city_tier, region.market, json.dumps(region.industries))
    )

async def load_regions_rows():
    async with get_db().execute("SELECT * FROM regions") as cursor:
        return await cursor.fetchall()
    
# ---------------

async def save_unit(unit: "Unit"):
    logger.debug(f"Saving unit at {unit.id}")
    if unit.id is None:
        async with get_db().execute(
            """
            INSERT INTO units (
                name, type, home, x, y,
                strength, morale, exp, owner,
                movement_free, status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                unit.name,
                unit.type,
                unit.home,
                unit.location[0],
                unit.location[1],
                unit.strength,
                unit.morale,
                unit.exp,
                unit.owner,
                unit.movement_free,
                unit.status
            )
        ) as cursor:
            unit.id = cursor.lastrowid
    else:
        await get_db().execute(
            """
            UPDATE units
            SET name = ?, type = ?, home = ?, x = ?, y = ?,
                strength = ?, morale = ?, exp = ?, owner = ?,
                movement_free = ?, status = ?
            WHERE id = ?
            """,
            (
                unit.name,
                unit.type,
                unit.home,
                unit.location[0],
                unit.location[1],
                unit.strength,
                unit.morale,
                unit.exp,
                unit.owner,
                unit.movement_free,
                unit.status,
                unit.id,
            )
        )

async def delete_unit(unit: "Unit"):
    if unit.id is not None:
        await get_db().execute("DELETE FROM units WHERE id = ?", (unit.id,))

async def load_units_rows():
    async with get_db().execute("SELECT * FROM units") as cursor:
        return await cursor.fetchall()

# ---------------

def encode_structure(structure: "Structure") -> dict:
    if structure is None:
        return {}
    
    return {
        "structure_type": structure.structure_type.name,
        "x": structure.location[0],
        "y": structure.location[1],
        "region": structure.region,
        "builder": structure.owner
    }

async def save_tile(tile: "Tile"):
    logger.debug(f"Saving tile at {tile.location}")
    x, y = tile.location
    await get_db().execute(
        """
        INSERT INTO tiles (
        x, y, terrain, owner, structure)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(x, y) DO UPDATE SET
            terrain = excluded.terrain,
            owner = excluded.owner,
            structure = excluded.structure
        """,
        (
            x, y, tile.terrain.data(), tile.owner,  
            json.dumps(encode_structure(tile.structure))
        )
    )

async def save_tiles(iterable_tiles):
    for tile in iterable_tiles:
        await save_tile(tile)

async def load_tiles_rows():
    async with get_db().execute("SELECT * FROM tiles") as cursor:
        return await cursor.fetchall()

# ---------------

async def save_economy(econ: "Econ"):
    logger.debug(f"Saving economy at {econ.nationid}")
    await get_db().execute(
        """
        INSERT INTO economies (nationid, influence, influence_cap)
        VALUES (?, ?, ?)
        ON CONFLICT(nationid) DO UPDATE SET
            influence = excluded.influence,
            influence_cap = excluded.influence_cap
        """,
        (econ.nationid, econ.influence, econ.influence_cap)
    )

async def load_economies_rows():
    async with get_db().execute("SELECT * FROM economies") as cursor:
        return await cursor.fetchall()
    
# ----------------

async def save_market(market: "Market"):
    logger.debug(f"Saving market at {market.id}")
    if market.id is None:
        async with get_db().execute(
            """
            INSERT INTO markets (
                name, owner, regions
            )
            VALUES (?, ?, ?)
            """,
            (
                market.name,
                market.owner,
                json.dumps(market.regions)
            )
        ) as cursor:
            market.id = cursor.lastrowid
    else:
        await get_db().execute(
            """
            UPDATE markets
            SET name = ?, owner = ?, regions = ?
            WHERE id = ?
            """,
            (
                market.name,
                market.owner,
                json.dumps(market.regions),
                market.id
            )
        )

async def delete_market(market: "Market"):
    if market.id is not None:
        await get_db().execute("DELETE FROM markets WHERE id = ?", (market.id,))

async def load_markets_rows():
    async with get_db().execute("SELECT * FROM markets") as cursor:
        return await cursor.fetchall()