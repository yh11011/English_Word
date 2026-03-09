#!/usr/bin/env python3
"""
Idempotent migration helper to add SRS columns and users table if missing.
Backs up the database before altering the schema.
Usage: python3 tools/migrate_add_srs.py [path/to/vocabulary.db]
"""

import sqlite3
import sys
import time
import shutil
import os
import logging

DB = sys.argv[1] if len(sys.argv) > 1 else os.environ.get('DB_NAME', 'vocabulary.db')

REQUIRED_WORDS_COLS = {
    'next_review': 'next_review INTEGER',
    'interval': "interval INTEGER DEFAULT 0",
    'efactor': "efactor REAL DEFAULT 2.5",
    'repetitions': "repetitions INTEGER DEFAULT 0",
    'owner_id': 'owner_id INTEGER'
}

logging.basicConfig(level=logging.INFO)


def get_columns(conn, table):
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info({table})")
    return [r[1] for r in cur.fetchall()]


def add_column(conn, table, col_def):
    logging.info("Adding column %s to %s", col_def, table)
    cur = conn.cursor()
    cur.execute(f"ALTER TABLE {table} ADD COLUMN {col_def}")
    conn.commit()


def ensure_users_table(conn):
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
    if cur.fetchone():
        logging.info("users table already exists")
        return
    cur.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at INTEGER DEFAULT (strftime('%s','now'))
        )
    """)
    conn.commit()
    logging.info("Created users table")


if __name__ == '__main__':
    if not os.path.exists(DB):
        logging.error("Database file not found: %s", DB)
        sys.exit(1)

    ts = int(time.time())
    bak = f"{DB}.bak.{ts}"
    shutil.copyfile(DB, bak)
    logging.info("Backed up %s -> %s", DB, bak)

    conn = sqlite3.connect(DB)

    # ensure words table exists
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='words'")
    if not cur.fetchone():
        logging.error("words table not found in %s", DB)
        conn.close()
        sys.exit(1)

    cols = get_columns(conn, 'words')
    missing = [k for k in REQUIRED_WORDS_COLS.keys() if k not in cols]
    if missing:
        logging.info("Missing columns: %s", missing)
        for k in missing:
            try:
                add_column(conn, 'words', REQUIRED_WORDS_COLS[k])
            except Exception:
                logging.exception("Failed to add %s", k)
    else:
        logging.info("No missing SRS columns")

    # ensure users table exists
    ensure_users_table(conn)

    # ensure owner index
    try:
        cur.execute("CREATE INDEX IF NOT EXISTS idx_words_owner_id ON words(owner_id)")
        conn.commit()
    except Exception:
        logging.exception("Failed to create owner index")

    conn.close()
    logging.info("Migration completed")
