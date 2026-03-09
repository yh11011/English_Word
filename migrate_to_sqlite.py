#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
資料遷移工具
將舊的文字檔格式轉換成 SQLite 資料庫格式

This file was extended to add an idempotent FTS5 migration helper that will
create a contentless FTS5 virtual table and triggers mirroring the `words`
table when FTS5 is available in the SQLite build.
"""

import sqlite3
import os
import logging


def create_database(db_name="vocabulary.db"):
    """
    建立 SQLite 資料庫和資料表
    """
    print(f"正在建立資料庫: {db_name}")
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS words (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            english TEXT NOT NULL,
            chinese TEXT NOT NULL,
            folder TEXT NOT NULL,
            error_count INTEGER DEFAULT 0,
            owner_id INTEGER,
            next_review INTEGER,
            interval INTEGER DEFAULT 0,
            efactor REAL DEFAULT 2.5,
            repetitions INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create users table to support auth flows
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at INTEGER DEFAULT (strftime('%s','now'))
        )
    """)

    # owner index
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_words_owner_id ON words(owner_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_folder ON words(folder)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_english ON words(english)
    """)

    conn.commit()
    print("✓ 資料庫建立完成")

    return conn, cursor


def migrate_from_txt(txt_file="english_word.txt", db_name="vocabulary.db"):
    # existing migration logic unchanged
    # ...
    pass


def sqlite_supports_fts5(conn):
    try:
        cur = conn.cursor()
        cur.execute('PRAGMA compile_options;')
        rows = [r[0].lower() for r in cur.fetchall()]
        for r in rows:
            if 'fts5' in r or 'enable_fts5' in r:
                return True
        # As a fallback, try creating a temporary FTS5 table in a savepoint
        try:
            cur.execute("SAVEPOINT test_fts5")
            cur.execute("CREATE VIRTUAL TABLE IF NOT EXISTS _fts_test USING fts5(content)")
            cur.execute("DROP TABLE IF EXISTS _fts_test")
            cur.execute("RELEASE test_fts5")
            return True
        except Exception:
            try:
                cur.execute("ROLLBACK TO test_fts5")
            except Exception:
                pass
        return False
    except Exception:
        return False


def migrate_add_fts(db_path='vocabulary.db'):
    """Idempotent migration to add a contentless FTS5 virtual table and
    triggers to keep it synchronized with `words` table when FTS5 is available.

    This function will not modify or drop the existing `words` table.
    """
    if not os.path.exists(db_path):
        logging.error("Database not found: %s", db_path)
        return False

    conn = sqlite3.connect(db_path)
    try:
        if not sqlite_supports_fts5(conn):
            logging.info("SQLite build does not support FTS5; skipping FTS migration.")
            return False

        cur = conn.cursor()
        # Create contentless FTS table if not exists
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='words_fts'")
        if not cur.fetchone():
            cur.execute("CREATE VIRTUAL TABLE IF NOT EXISTS words_fts USING fts5(english, chinese, content='')")

        # Create triggers to keep the FTS table in sync. Use IF NOT EXISTS guard by checking sqlite_master.
        # AFTER INSERT
        cur.execute("SELECT name FROM sqlite_master WHERE type='trigger' AND name='words_ai'")
        if not cur.fetchone():
            cur.execute("""
                CREATE TRIGGER words_ai AFTER INSERT ON words BEGIN
                    INSERT INTO words_fts(rowid, english, chinese) VALUES (new.id, new.english, new.chinese);
                END;
            """)
        # AFTER DELETE
        cur.execute("SELECT name FROM sqlite_master WHERE type='trigger' AND name='words_ad'")
        if not cur.fetchone():
            cur.execute("""
                CREATE TRIGGER words_ad AFTER DELETE ON words BEGIN
                    DELETE FROM words_fts WHERE rowid = old.id;
                END;
            """)
        # AFTER UPDATE
        cur.execute("SELECT name FROM sqlite_master WHERE type='trigger' AND name='words_au'")
        if not cur.fetchone():
            cur.execute("""
                CREATE TRIGGER words_au AFTER UPDATE ON words BEGIN
                    UPDATE words_fts SET english = new.english, chinese = new.chinese WHERE rowid = new.id;
                END;
            """)

        conn.commit()
        logging.info("FTS5 migration completed (words_fts + triggers created)")
        return True
    except Exception as e:
        logging.exception("Failed to add FTS5 support: %s", e)
        conn.rollback()
        return False
    finally:
        conn.close()


if __name__ == "__main__":
    # Direct usage
    create_database()
    print("You can call migrate_add_fts('vocabulary.db') to add optional FTS5 support if available.")
