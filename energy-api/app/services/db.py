# app/services/db.py
import os
import logging
from contextlib import contextmanager
import psycopg2
from psycopg2.extras import RealDictCursor

log = logging.getLogger(__name__)

def get_conn():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", "5432")),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        sslmode=os.getenv("DB_SSLMODE", "disable"),
        connect_timeout=3,
    )

@contextmanager
def get_cursor(dict_cursor=True):
    conn = get_conn()
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor if dict_cursor else None)
        yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        log.exception("DB error")
        raise
    finally:
        conn.close()

def fetch_one(sql, params=()):
    with get_cursor(True) as cur:
        cur.execute(sql, params)
        return cur.fetchone()

def fetch_all(sql, params=()):
    with get_cursor(True) as cur:
        cur.execute(sql, params)
        return cur.fetchall()

def execute(sql, params=()):
    with get_cursor(False) as cur:
        cur.execute(sql, params)

