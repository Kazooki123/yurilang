"""
SQlite3 - Yurilang

Uses python's built-in `sqlite3` module. DLL support soon.
"""

import sqlite3 as _sqlite3

_connections = {}
_cursors     = {}
_active      = None

def connect(path, name="default"):
    global _active
    conn = _sqlite3.connect(path)
    _connections[name] = conn
    _cursors[name]     = conn.cursor()
    _active            = name
    return name

def vow(sql, params=None, name=None):
    name    = name or _active
    cursor  = _cursors.get(name)
    if cursor is None:
        raise RuntimeError(f"No active DB connection: '{name}' - use @connect first")
    if params:
        cursor.execute(sql, params)
    else:
        cursor.execute(sql)
    return cursor

def remember(name=None):
    name    = name or _active
    cursor  = _cursors.get(name)
    if cursor is None:
        raise RuntimeError(f"No active DB connection: '{name}'")
    return [list(row) for row in cursor.fetchall()]

def glimpse(name=None):
    name    = name or _active
    cursor  = _cursors.get(name)
    if cursor is None:
        raise RuntimeError(f"No active DB connection: '{name}'")
    row = cursor.fetchone()
    return list(row) if row else None
    
def seal(name=None):
    name    = name or _active
    conn    = _connections.get(name)
    if conn is None:
        raise RuntimeError(f"No active DB connection: '{name}'")
    conn.commit()

def farewell(name=None):
    global _active
    name    = name or _active
    conn    = _connections.get(name)
    if conn:
        conn.close()
        del _connections[name]
        del _cursors[name]
    if _active == name:
        _active = None

def row_count(name=None):
    name    = name or _active
    cursor  = _cursors.get(name)
    return cursor.rowcount if cursor else 0

SQLITE_OPS = {
    "connect":   connect,
    "vow":       vow,
    "remember":  remember,
    "glimpse":   glimpse,
    "seal":      seal,
    "farewell":  farewell,
    "row_count": row_count,
}
