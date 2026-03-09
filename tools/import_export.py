#!/usr/bin/env python3
"""
Small utilities for CSV import/export used by CLI or scripts.
Usage examples:
  python3 tools/import_export.py export /path/to/db > export.csv
  python3 tools/import_export.py import /path/to/db file.csv
"""
import csv
import sqlite3
import sys
import os

DB = sys.argv[2] if len(sys.argv) > 2 else os.environ.get('DB_NAME', 'vocabulary.db')


def export_csv(path):
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT id, english, chinese, folder, error_count, created_at, next_review, interval, efactor, repetitions FROM words ORDER BY folder, english")
    rows = cur.fetchall()
    w = csv.writer(sys.stdout)
    w.writerow(['id','english','chinese','folder','error_count','created_at','next_review','interval','efactor','repetitions'])
    for r in rows:
        w.writerow([r['id'], r['english'], r['chinese'], r['folder'], r['error_count'], r['created_at'], r['next_review'], r['interval'], r['efactor'], r['repetitions']])


def import_csv(path, csvfile):
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    added = 0
    with open(csvfile, newline='', encoding='utf-8') as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            english = (row.get('english') or '').strip().lower()
            chinese = (row.get('chinese') or '').strip()
            folder = (row.get('folder') or '').strip().lower() or 'imported'
            if not english or not chinese:
                continue
            cur.execute('SELECT id FROM words WHERE folder = ? AND english = ?', (folder, english))
            if cur.fetchone():
                continue
            cur.execute('INSERT INTO words (english, chinese, folder, error_count) VALUES (?, ?, ?, 0)', (english, chinese, folder))
            added += 1
    conn.commit()
    print(f"Imported: {added}")


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: import_export.py [export|import] /path/to/db [file.csv]")
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == 'export':
        export_csv(sys.argv[2])
    elif cmd == 'import':
        import_csv(sys.argv[2], sys.argv[3])
    else:
        print("Unknown command")
