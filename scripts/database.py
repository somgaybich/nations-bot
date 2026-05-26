import aiosqlite
import json
import logging
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from game.nation import Nation
    from game.authority import Authority
    from game.economy import Econ
    from game.military import Unit
    from game.region import Region
    from world.map import Tile
    from world.structures import Structure

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
        inventory TEXT,
        authority TEXT,
        capital TEXT,
        city_tier INTEGER)
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
        owner INTEGER,
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
        CREATE TABLE IF NOT EXISTS authorities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            nationid INTEGER NOT NULL,
            authtype TEXT NOT NULL,
            cap INTEGER NOT NULL,
            cooperation FLOAT NOT NULL,
            region TEXT NOT NULL)
        """)
    logger.debug("Created authorities table")

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
    logger.debug(f"Saving nation at {region.name}")
    encoded_inventory = []
    for item in region.inventory:
        encoded_inventory.append(item.encode())
    await get_db().execute(
        """
        INSERT INTO regions (
            name, x, y, owner, tiles, inventory, authority, capital, 
            city_tier, infrastructure, trades)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(name) DO UPDATE SET
            name = excluded.name,
            tiles = excluded.tiles,
            inventory = excluded.inventory,
            authority = excluded.authority,
            city_tier = excluded.city_tier,
            infrastructure = excluded.infrastructure,
            trades = excluded.trades
        """,
        (region.name, region.location[0], region.location[1], region.owner, 
         json.dumps(region.tiles), json.dumps(encoded_inventory), 
         region.authority, json.dumps(region.is_capital), region.city_tier, 
         region.infrastructure, region.trades)
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

async def save_authority(authority: "Authority"):
    logger.debug(f"Saving authority at {authority.id}")
    if authority.id is None:
        async with get_db().execute(
            """
            INSERT INTO authorities (
                name, nationid, authtype, cooperation, region
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                authority.name,
                authority.nationid,
                authority.authtype,
                authority.cooperation,
                authority.region
            )
        ) as cursor: 
            authority.id = cursor.lastrowid
    else:
        await get_db().execute(
            """
            UPDATE authorities
            SET name = ?, nationid = ?, authtype = ?, region = ?, 
                cooperation = ?
            WHERE id = ?
            """,
            (
                authority.name,
                authority.nationid,
                authority.authtype,
                authority.region,
                authority.cooperation,
                authority.id
            )
        )

async def delete_authority(authority: "Authority"):
    if authority.id is not None:
        await get_db().execute("DELETE FROM authorities WHERE id = ?", (authority.id))

async def load_authorities_rows():
    async with get_db().execute("SELECT * FROM authorities") as cursor:
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