import aiosqlite
import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)

_db: Optional[aiosqlite.Connection] = None

async def init_db():
    logger.info("Starting database connection")
    global _db
    if _db is not None:
        return
    
    _db = await aiosqlite.connect("data/nations.db")
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
        owned BOOLEAN,
        structures TEXT,
        PRIMARY KEY (x, y))
    """)
    logger.debug("Created tiles table")

    await _db.execute(
    """
    CREATE TABLE IF NOT EXISTS cities (
        x INTEGER NOT NULL,
        y INTEGER NOT NULL,
        name TEXT NOT NULL,
        influence INTEGER NOT NULL,
        tier INTEGER NOT NULL,
        stability INTEGER NOT NULL,
        popularity INTEGER NOT NULL,
        inventory TEXT NOT NULL,
        owner INTEGER NOT NULL,
        structures TEXT NOT NULL,
        PRIMARY KEY (x, y))
    """)
    logger.debug("Created cities table")

    await _db.execute(
    """
    CREATE TABLE IF NOT EXISTS links (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        linktype TEXT NOT NULL,
        origin TEXT NOT NULL,
        destination TEXT NOT NULL,
        path TEXT NOT NULL,
        owner INTEGER NOT NULL)
    """)
    logger.debug("Created links table")
        
    await _db.execute(
        """
        CREATE TABLE IF NOT EXISTS economies (
            nationid INTEGER PRIMARY KEY,
            influence INTEGER NOT NULL,
            influence_cap INTEGER NOT NULL)
        """)
    logger.debug("Created economies table")

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

async def save_nation(nation):
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

async def save_unit(unit):
    logger.debug(f"Saving unit at {unit.id}")
    if unit.id is None:
        async with get_db().execute(
            """
            INSERT INTO units (
                name, unit_type, home, x, y,
                strength, morale, exp, owner
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            )
        ) as cursor:
            unit.id = cursor.lastrowid
    else:
        await get_db().execute(
            """
            UPDATE units
            SET name = ?, unit_type = ?, home = ?, x = ?, y = ?,
                strength = ?, morale = ?, exp = ?, owner = ?
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
                unit.id,
            )
        )

async def delete_unit(unit):
    if unit.id is not None:
        await get_db().execute("DELETE FROM units WHERE id = ?", (unit.id,))

async def load_units_rows():
    async with get_db().execute("SELECT * FROM units") as cursor:
        return await cursor.fetchall()

# ---------------

async def save_tile(tile):
    logger.debug(f"Saving tile at {tile.location}")
    x, y = tile.location
    await get_db().execute(
        """
        INSERT INTO tiles (
        x, y, terrain, owner, owned, structures
        )
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(x, y) DO UPDATE SET
            terrain = excluded.terrain,
            owner = excluded.owner,
            owned = excluded.owned,
            structures = excluded.structures
        """,
        (x, y, tile.terrain, tile.owner, tile.owned, json.dumps(tile.structures))
    )

async def save_tiles(iterable_tiles):
    for tile in iterable_tiles:
        await save_tile(tile)

async def load_tiles_rows():
    async with get_db().execute("SELECT * FROM units") as cursor:
        return await cursor.fetchall()

# ---------------

async def save_city(city):
    logger.debug(f"Saving city at {city.location}")
    x, y = city.location
    await get_db().execute(
        """
        INSERT INTO cities (
        x, y, name, influence, tier, stability, popularity, inventory, owner, structures
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(x, y) DO UPDATE SET
            name = excluded.name,
            influence = excluded.influence,
            tier = excluded.tier,
            stability = excluded.stability,
            popularity = excluded.popularity,
            inventory = excluded.inventory,
            owner = excluded.owner,
            structures = excluded.structures
        """,
        (x, y, city.name, city.influence, city.tier, city.stability, city.popularity, 
         json.dumps(city.inventory), city.owner, json.dumps(city.structures))
    )

async def load_cities_rows():
    async with get_db().execute("SELECT * FROM cities") as cursor:
        return await cursor.fetchall()

# ---------------

async def save_link(link):
    logger.debug(f"Saving link at {link.id}")
    if link.id is None:
        async with get_db().execute(
            """
            INSERT INTO links (linktype, origin, destination, path, owner)
            VALUES (?, ?, ?, ?, ?)
            """,
            (link.linktype, link.origin, link.destination, json.dumps(link.path), link.owner)
        ) as cursor:
            link.id = cursor.lastrowid
    else:
        await get_db().execute(
            """
            UPDATE linktype = ?, origin = ?, destination = ?, path = ?, owner = ?
            WHERE id = ?
            """,
            (link.linktype, link.origin, link.destination, json.dumps(link.path), link.owner, link.id)
        )

async def delete_link(link):
    if link.id is not None:
        await get_db().execute("DELETE FROM links WHERE id = ?", (link.id,))

async def load_links_rows():
    async with get_db().execute("SELECT * FROM links") as cursor:
        return await cursor.fetchall()

# ---------------

async def save_economy(econ):
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