import sqlite3
import json

conn = sqlite3.connect('data/nations.db')
conn.execute("PRAGMA foreign_keys = ON;")
conn.row_factory = sqlite3.Row


conn.execute("""
CREATE TABLE IF NOT EXISTS nations (
             id INTEGER PRIMARY KEY,
             name TEXT NOT NULL,
             dossier TEXT)""")

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


conn.execute("""
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
             owner INTEGER NOT NULL)""")

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


conn.execute("""
CREATE TABLE IF NOT EXISTS tiles (
             x INTEGER NOT NULL,
             y INTEGER NOT NULL,
             terrain TEXT NOT NULL,
             owner INTEGER,
             owned BOOLEAN,
             upgrades TEXT,
             PRIMARY KEY (x, y))""")

def save_tiles():
    pass

def load_tiles_rows():
    return conn.execute("SELECT * FROM units").fetchall()


conn.execute("""
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
             PRIMARY KEY (x, y))""")

def save_cities():
    pass

def load_cities_rows():
    return conn.execute("SELECT * FROM units").fetchall()


conn.execute("""
CREATE TABLE IF NOT EXISTS subdivision_cities (
             subdivisionid INTEGER NOT NULL,
             cityx INTEGER NOT NULL,
             cityy INTEGER NOT NULL)""")

def save_subdivision_cities():
    pass

def load_subdivision_cities_rows():
    return conn.execute("SELECT * FROM subdivision_cities").fetchall()

conn.execute("""
CREATE TABLE IF NOT EXISTS subdivisions (
             id INTEGER PRIMARY KEY AUTOINCREMENT,
             name TEXT NOT NULL,
             nationid INTEGER NOT NULL)""")

def save_subdivisions():
    pass

def load_subdivisions_rows():
    return conn.execute("SELECT * FROM subdivisions").fetchall()


conn.execute("""
CREATE TABLE IF NOT EXISTS links (
             id INTEGER PRIMARY KEY AUTOINCREMENT,
             linktype TEXT NOT NULL,
             origin TEXT NOT NULL,
             destination TEXT NOT NULL,
             path TEXT NOT NULL,
             owner INTEGER NOT NULL)""")

def save_links():
    pass

def load_links_rows():
    return conn.execute("SELECT * FROM links").fetchall()


conn.execute("""
CREATE TABLE IF NOT EXISTS governments (
             nationid INTEGER PRIMARY KEY,
             influence INTEGER NOT NULL,
             influence_cap INTEGER NOT NULL,
             systems TEXT NOT NULL,
             streaks TEXT NOT NULL,
             events TEXT NOT NULL)""")

def save_governments():
    pass

def load_governments_rows():
    return conn.execute("SELECT * FROM governments").fetchall()


conn.execute("""
CREATE TABLE IF NOT EXISTS economies (
             nationid INTEGER PRIMARY KEY,
             influence INTEGER NOT NULL,
             influence_cap INTEGER NOT NULL)""")

def save_economies():
    pass

def load_economies_rows():
    return conn.execute("SELECT * FROM economies").fetchall()

conn.commit()