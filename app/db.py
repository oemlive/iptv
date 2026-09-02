import sqlite3, json, os
from datetime import datetime, timezone
from .config import settings
from .models import Source

SCHEMA='''CREATE TABLE IF NOT EXISTS sources(id TEXT PRIMARY KEY, payload TEXT NOT NULL, updated_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS checks(id INTEGER PRIMARY KEY AUTOINCREMENT, source_id TEXT, checked_at TEXT, valid INTEGER, score INTEGER, latency_ms INTEGER, error TEXT);'''

def now(): return datetime.now(timezone.utc).isoformat()

def connect():
    os.makedirs(os.path.dirname(settings.database) or ".",exist_ok=True)
    c=sqlite3.connect(settings.database); c.executescript(SCHEMA); return c

def upsert(items):
    c=connect()
    for x in items: c.execute("INSERT INTO sources VALUES(?,?,?) ON CONFLICT(id) DO UPDATE SET payload=excluded.payload,updated_at=excluded.updated_at",(x.id,x.model_dump_json(),now()))
    c.commit(); c.close()

def all_sources():
    c=connect(); rows=c.execute("SELECT payload FROM sources").fetchall(); c.close(); return [Source.model_validate_json(r[0]) for r in rows]

def record_check(x):
    c=connect(); c.execute("INSERT INTO checks(source_id,checked_at,valid,score,latency_ms,error) VALUES(?,?,?,?,?,?)",(x.id,now(),int(bool(x.valid)),x.score,x.latency_ms,x.last_error)); c.commit(); c.close()
