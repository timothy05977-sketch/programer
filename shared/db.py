"""SQLite persistence — products list + historical snapshots."""
from __future__ import annotations
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "tracker.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS products (
    asin        TEXT PRIMARY KEY,
    label       TEXT,
    category    TEXT,
    added_at    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS snapshots (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    asin          TEXT NOT NULL,
    title         TEXT,
    price         TEXT,
    price_value   REAL,
    rating        TEXT,
    review_count  TEXT,
    availability  TEXT,
    sales_rank    INTEGER,
    rank_category TEXT,
    data_source   TEXT,
    fetched_at    TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_snap_asin ON snapshots(asin);
CREATE INDEX IF NOT EXISTS idx_snap_time ON snapshots(asin, fetched_at);
"""


@dataclass
class Product:
    asin: str
    label: str
    category: str
    added_at: str


@dataclass
class Snapshot:
    asin: str
    title: str
    price: str
    price_value: float | None
    rating: str
    review_count: str
    availability: str
    sales_rank: int | None
    rank_category: str
    data_source: str  # "rainforest" | "scraper"
    fetched_at: str


@contextmanager
def _conn():
    con = sqlite3.connect(str(DB_PATH))
    con.row_factory = sqlite3.Row
    try:
        yield con
        con.commit()
    finally:
        con.close()


def init() -> None:
    with _conn() as con:
        con.executescript(_SCHEMA)


# ── Products ──────────────────────────────────────────────────────────────────

def add_product(asin: str, label: str = "", category: str = "") -> None:
    with _conn() as con:
        con.execute(
            "INSERT OR REPLACE INTO products (asin, label, category, added_at) VALUES (?,?,?,?)",
            (asin.strip().upper(), label, category, datetime.utcnow().isoformat()),
        )


def remove_product(asin: str) -> bool:
    with _conn() as con:
        cur = con.execute("DELETE FROM products WHERE asin = ?", (asin.strip().upper(),))
        return cur.rowcount > 0


def list_products() -> list[Product]:
    with _conn() as con:
        rows = con.execute("SELECT * FROM products ORDER BY added_at").fetchall()
    return [Product(**dict(r)) for r in rows]


def update_product_label(asin: str, label: str) -> None:
    with _conn() as con:
        con.execute("UPDATE products SET label = ? WHERE asin = ?", (label, asin.upper()))


# ── Snapshots ─────────────────────────────────────────────────────────────────

def save_snapshot(snap: Snapshot) -> None:
    with _conn() as con:
        con.execute(
            """INSERT INTO snapshots
               (asin, title, price, price_value, rating, review_count,
                availability, sales_rank, rank_category, data_source, fetched_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (snap.asin, snap.title, snap.price, snap.price_value, snap.rating,
             snap.review_count, snap.availability, snap.sales_rank,
             snap.rank_category, snap.data_source, snap.fetched_at),
        )


def get_recent_snapshots(asin: str, limit: int = 10) -> list[dict]:
    with _conn() as con:
        rows = con.execute(
            "SELECT * FROM snapshots WHERE asin = ? ORDER BY fetched_at DESC LIMIT ?",
            (asin, limit),
        ).fetchall()
    return [dict(r) for r in rows]


def get_history(asin: str, limit: int = 50) -> list[dict]:
    return get_recent_snapshots(asin, limit)
