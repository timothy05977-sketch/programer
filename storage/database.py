from __future__ import annotations
import sqlite3
from contextlib import contextmanager
from config import DB_PATH
from scraper.product import ProductSnapshot


_SCHEMA = """
CREATE TABLE IF NOT EXISTS snapshots (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    asin        TEXT NOT NULL,
    title       TEXT,
    price       TEXT,
    rating      TEXT,
    review_count TEXT,
    availability TEXT,
    sales_rank  TEXT,
    fetched_at  TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_snapshots_asin ON snapshots(asin);
CREATE INDEX IF NOT EXISTS idx_snapshots_time ON snapshots(asin, fetched_at);
"""


@contextmanager
def _conn():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    try:
        yield con
        con.commit()
    finally:
        con.close()


def init_db() -> None:
    with _conn() as con:
        con.executescript(_SCHEMA)


def save_snapshot(snap: ProductSnapshot) -> None:
    with _conn() as con:
        con.execute(
            """INSERT INTO snapshots
               (asin, title, price, rating, review_count, availability, sales_rank, fetched_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (snap.asin, snap.title, snap.price, snap.rating,
             snap.review_count, snap.availability, snap.sales_rank, snap.fetched_at),
        )


def get_history(asin: str, limit: int = 50) -> list[dict]:
    with _conn() as con:
        rows = con.execute(
            "SELECT * FROM snapshots WHERE asin = ? ORDER BY fetched_at DESC LIMIT ?",
            (asin, limit),
        ).fetchall()
    return [dict(r) for r in rows]


def list_tracked_asins() -> list[str]:
    with _conn() as con:
        rows = con.execute(
            "SELECT DISTINCT asin FROM snapshots ORDER BY asin"
        ).fetchall()
    return [r["asin"] for r in rows]
