import os
import tempfile
import sqlite3
from migrate_to_sqlite import create_database, migrate_add_fts


def test_create_database_and_basic_ops(tmp_path):
    db_file = tmp_path / "test_vocab.db"
    conn, cur = create_database(str(db_file))
    # Insert a row
    cur.execute("INSERT INTO words (english, chinese, folder, error_count) VALUES (?, ?, ?, ?)", ('apple', '蘋果', 'fruits', 0))
    conn.commit()
    cur.execute("SELECT english, chinese, folder FROM words WHERE english = ?", ('apple',))
    row = cur.fetchone()
    assert row[0] == 'apple'
    assert row[1] == '蘋果'
    assert row[2] == 'fruits'
    conn.close()


def test_migrate_add_fts_no_error(tmp_path):
    db_file = tmp_path / "test_vocab.db"
    conn, cur = create_database(str(db_file))
    conn.close()
    # Should not raise even if FTS5 not available in test environment
    migrated = migrate_add_fts(str(db_file))
    assert migrated in (True, False)
