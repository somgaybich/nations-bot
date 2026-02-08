import aiosqlite
import json
import logging
from typing import Optional

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
        structure TEXT,
        link_structures TEXT,
        PRIMARY KEY (x, y))
    """)
    logger.debug("Created tiles table")

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

    await _db.execute(
        """
        CREATE TABLE IF NOT EXISTS authorities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            nationid INTEGER NOT NULL,
            authtype TEXT NOT NULL,
            cap INTEGER NOT NULL,
            cities TEXT NOT NULL)
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
                name, type, home, x, y,
                strength, morale, exp, owner,
                movement_free
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                unit.movement_free
            )
        ) as cursor:
            unit.id = cursor.lastrowid
    else:
        await get_db().execute(
            """
            UPDATE units
            SET name = ?, type = ?, home = ?, x = ?, y = ?,
                strength = ?, morale = ?, exp = ?, owner = ?,
                movement_free = ?
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

async def save_authority(authority):
    logger.debug(f"Saving authority at {authority.id}")
    if authority.id is None:
        async with get_db().execute(
            """
            INSERT INTO authorities (
                name, nationid, authtype, cap,
                cities
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                authority.name,
                authority.nationid,
                authority.authtype,
                authority.cap
            )
        ) as cursor: 
            authority.id = cursor.lastrowid
    else:
        await get_db().execute(
            """
            UPDATE authorities
            SET name = ?, nationid = ?, authtype = ?, cap = ?, cities = ?
            WHERE id = ?
            """,
            (
                authority.name,
                authority.nationid,
                authority.authtype,
                authority.cap,
                authority.cities,
                authority.id
            )
        )

async def delete_authority(authority):
    if authority.id is not None:
        await get_db().execute("DELETE FROM authorities WHERE id = ?", (authority.id))

async def load_authorities_rows():
    async with get_db().execute("SELECT * FROM authorities") as cursor:
        return await cursor.fetchall()

# ---------------

def encode_link_structures(link_structure_list) -> list:
    encoded_link_structures = []
    for link_structure in link_structure_list:
        encoded_link_structures.append({
            "structure_type": link_structure.structure_type.name,
            "x": link_structure.location[0],
            "y": link_structure.location[1],
            "root_city": link_structure.root_city,
            "builder": link_structure.builder
        })
    return encoded_link_structures

def encode_structure(structure) -> dict:
    if hasattr(structure, "name"):
        # This structure is a City
        encoded_inventory = []
        for item in structure.inventory:
            encoded_inventory.append(item.encode())
        return {
            "name": structure.name,
            "tier": structure.tier,
            "x": structure.location[0],
            "y": structure.location[1],
            "owner": structure.owner,
            "stability": structure.stability,
            "inventory": encoded_inventory,
            "authority": structure.authority
        }
    else:
        return {
            "structure_type": structure.structure_type.name,
            "x": structure.location[0],
            "y": structure.location[1],
            "root_city": structure.root_city,
            "builder": structure.builder
        }

async def save_tile(tile):
    logger.debug(f"Saving tile at {tile.location}")
    x, y = tile.location
    await get_db().execute(
        """
        INSERT INTO tiles (
        x, y, terrain, owner, owned, structure, link_structures
        )
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(x, y) DO UPDATE SET
            terrain = excluded.terrain,
            owner = excluded.owner,
            owned = excluded.owned,
            structure = excluded.structure,
            link_structures = excluded.link_structures
        """,
        (x, y, tile.terrain.data(), tile.owner, tile.owned, 
         encode_structure(tile.structure),
         encode_link_structures(tile.link_structures))
    )

async def save_tiles(iterable_tiles):
    for tile in iterable_tiles:
        await save_tile(tile)

async def load_tiles_rows():
    async with get_db().execute("SELECT * FROM tiles") as cursor:
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
            (link.linktype, link.origin.name, link.destination.name, json.dumps(link.path), link.owner)
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