import sqlite3
import json

conn = sqlite3.connect('data/nations.db')
conn.execute("PRAGMA foreign_keys = ON;")
conn.row_factory = sqlite3.Row

# ---------------

conn.execute(
    """
    CREATE TABLE IF NOT EXISTS nations (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        dossier TEXT)
    """
)

def save_nation(nation):
    conn.execute(
        """
        INSERT INTO nations (id, name, dossier)
        VALUES (?, ?, ?)
        ON CONFLICT (id) DO UPDATE SET
            name = excluded.name
            dossier = excluded.dossier
        """,
        (nation.userid, nation.name, nation.dossier)
    )

def load_nations_rows():
    cursor = conn.execute("SELECT * FROM nations")
    return cursor.fetchall()

# ---------------

conn.execute(
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
    """
)

def save_unit(unit):
    if unit.id is None:
        cursor = conn.execute(
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
        )
        unit.id = cursor.lastrowid
    else:
        conn.execute(
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

def delete_unit(unit):
    if unit.id is not None:
        conn.execute("DELETE FROM units WHERE id = ?", (unit.id,))

def load_units_rows():
    return conn.execute("SELECT * FROM units").fetchall()

# ---------------

conn.execute(
    """
    CREATE TABLE IF NOT EXISTS tiles (
        x INTEGER NOT NULL,
        y INTEGER NOT NULL,
        terrain TEXT NOT NULL,
        owner INTEGER,
        owned BOOLEAN,
        upgrades TEXT,
        PRIMARY KEY (x, y))
    """
)

def save_tile(tile):
    x, y = tile.location
    conn.execute(
        """
        INSERT INTO tiles (
        x, y, terrain, owner, owned, upgrades
        )
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(x, y) DO UPDATE SET
            terrain = excluded.terrain
            owner = excluded.owner
            owned = excluded.owned
            upgrades = excluded.upgrades
        """,
        (x, y, tile.terrain, tile.owner, tile.owned, json.dumps(tile.upgrades))
    )

def save_tiles(iterable_tiles):
    for tile in iterable_tiles:
        save_tile(tile)

def load_tiles_rows():
    return conn.execute("SELECT * FROM units").fetchall()

# ---------------

conn.execute(
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
        upgrades TEXT NOT NULL,
        PRIMARY KEY (x, y))
    """
)

def save_city(city):
    x, y = city.location
    conn.execute(
        """
        INSERT INTO cities (
        x, y, name, influence, tier, stability, popularity, inventory, owner, upgrades
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(x, y) DO UPDATE SET
            name = excluded.name
            influence = excluded.influence
            tier = excluded.tier
            stability = excluded.stability
            popularity = excluded.popularity
            inventory = excluded.inventory
            owner = excluded.owner
            upgrades = excluded.upgrades
        """,
        (x, y, city.name, city.influence, city.tier, city.stability, city.popularity, 
         json.dumps(city.inventory), city.owner, json.dumps(city.upgrades))
    )

def load_cities_rows():
    return conn.execute("SELECT * FROM units").fetchall()

# ---------------

conn.execute(
    """
    CREATE TABLE IF NOT EXISTS subdivisions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        nationid INTEGER NOT NULL,
        cities TEXT NOT NULL)
    """
)

def save_subdivision(subdivision):
    if subdivision.id is None:
        cursor = conn.execute(
            """
            INSERT INTO subdivisions (name, nationid, cities)
            VALUES (?, ?, ?)
            """,
            (subdivision.name, subdivision.nationid, json.dumps(subdivision.cities))
        )
        subdivision.id = cursor.lastrowid
    else:
        conn.execute(
            """
            UPDATE name = ?, nationid = ?, cities = ?
            WHERE id = ?
            """,
            (subdivision.name, subdivision.nationid, json.dumps(subdivision.cities), subdivision.id)
        )
        
def delete_subdivision(subdivision):
    if subdivision.id is not None:
        conn.execute("DELETE FROM subdivisions WHERE id = ?", (subdivision.id,))

def load_subdivisions_rows():
    return conn.execute("SELECT * FROM subdivisions").fetchall()

# ---------------

conn.execute(
    """
    CREATE TABLE IF NOT EXISTS links (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        linktype TEXT NOT NULL,
        origin TEXT NOT NULL,
        destination TEXT NOT NULL,
        path TEXT NOT NULL,
        owner INTEGER NOT NULL)
    """
)

def save_link(link):
    if link.id is None:
        cursor = conn.execute(
            """
            INSERT INTO links (linktype, origin, destination, path, owner)
            VALUES (?, ?, ?, ?, ?)
            """,
            (link.linktype, link.origin, link.destination, json.dumps(link.path), link.owner)
        )
        link.id = cursor.lastrowid
    else:
        conn.execute(
            """
            UPDATE linktype = ?, origin = ?, destination = ?, path = ?, owner = ?
            WHERE id = ?
            """,
            (link.linktype, link.origin, link.destination, json.dumps(link.path), link.owner, link.id)
        )

def delete_link(link):
    if link.id is not None:
        conn.execute("DELETE FROM links WHERE id = ?", (link.id,))

def load_links_rows():
    return conn.execute("SELECT * FROM links").fetchall()

# ---------------

conn.execute(
    """
    CREATE TABLE IF NOT EXISTS governments (
        nationid INTEGER PRIMARY KEY,
        influence INTEGER NOT NULL,
        influence_cap INTEGER NOT NULL,
        systems TEXT NOT NULL,
        streaks TEXT NOT NULL,
        events TEXT NOT NULL)
    """
)

def save_government(gov):
    conn.execute(
        """
        INSERT INTO governments (
        nationid, influence, influence_cap, systems, streaks, events)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(nationid) DO UPDATE SET
            influence = excluded.influence
            influence_cap = excluded.influence_cap
            systems = excluded.systems
            streaks = excluded.streaks
            events = excluded.events
        """,
        (gov.nationid, gov.influence, gov.influence_cap, gov.systems, gov.streaks, gov.events)
    )

def load_governments_rows():
    return conn.execute("SELECT * FROM governments").fetchall()

# ---------------

conn.execute(
    """
    CREATE TABLE IF NOT EXISTS economies (
        nationid INTEGER PRIMARY KEY,
        influence INTEGER NOT NULL,
        influence_cap INTEGER NOT NULL)
    """
)

def save_economies():
    conn.execute(
        """
        INSERT INTO economies (nationid, influence, influence_cap)
        VALUES (?, ?, ?)
        ON CONFLICT(nationid) DO UPDATE SET
            influence = excluded.influence
            influence_cap = excluded.influence_cap
        """
    )

def load_economies_rows():
    return conn.execute("SELECT * FROM economies").fetchall()

conn.commit()