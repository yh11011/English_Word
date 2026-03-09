#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
英文單字背誦系統 - 網頁版後端 (Flask)
提供 RESTful API 和網頁介面

This file was updated to add optional FTS5 search support, token-based API
authentication, CSRF protection for browser mutating requests, small caching
helpers and safer DB patterns. Added minimal SRS (SM-2 inspired) support with
an auto-migrate gate controlled by MIGRATE_SRS environment variable.
"""

from flask import Flask, render_template, request, jsonify, session, g
import sqlite3
import random
import os
from datetime import datetime
import secrets
import logging
from functools import lru_cache, wraps
import time

app = Flask(__name__)
# Load secrets from environment; fall back to a random key for quick dev but log a warning
SECRET_KEY = os.environ.get('SECRET_KEY')
API_TOKEN = os.environ.get('API_TOKEN')
if not SECRET_KEY:
    logging.warning("SECRET_KEY not set in environment — using a random key. Do not use in production.")
    SECRET_KEY = os.urandom(24)
app.secret_key = SECRET_KEY

if not API_TOKEN:
    logging.warning("API_TOKEN not set in environment — mutating API will require CSRF from browsers only.")

# 資料庫設定
DB_NAME = os.environ.get('DB_NAME', 'vocabulary.db')
# Gate automatic SRS migration: set MIGRATE_SRS=1 to allow ALTER TABLE to add SRS columns
MIGRATE_SRS = os.environ.get('MIGRATE_SRS', '0') == '1'


# ------------------ DB helpers ------------------
def get_db():
    """取得資料庫連線並綁定到 flask.g，確保在 app context 結束時關閉。"""
    if hasattr(g, 'db') and g.db:
        return g.db
    # 增加 timeout 並啟用 row_factory
    conn = sqlite3.connect(DB_NAME, timeout=30)
    conn.row_factory = sqlite3.Row
    # 優化：開啟 WAL 模式以改善併發（忽略錯誤）
    try:
        conn.execute('PRAGMA journal_mode=WAL;')
    except Exception:
        pass
    g.db = conn
    return conn


def init_db():
    """初始化資料庫"""
    conn = get_db()
    cursor = conn.cursor()

    # 建立資料表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS words (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            english TEXT NOT NULL,
            chinese TEXT NOT NULL,
            folder TEXT NOT NULL,
            error_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 建立索引
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_folder ON words(folder)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_english ON words(english)
    """)

    conn.commit()

    # Ensure SRS columns exist. If MIGRATE_SRS=1 then automatically ALTER TABLE to add missing columns.
    try:
        ensure_srs_columns(conn)
    except Exception as e:
        logging.exception("SRS migration failed or skipped: %s", e)


# ------------------ SRS / migration helpers ------------------

def _get_table_columns(conn, table_name):
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(%s)" % table_name)
    return [r['name'] for r in cur.fetchall()]


def _add_column(conn, table, column_def):
    # column_def should be like "next_review INTEGER"
    cur = conn.cursor()
    sql = f"ALTER TABLE {table} ADD COLUMN {column_def}"
    cur.execute(sql)
    conn.commit()


def ensure_srs_columns(conn):
    """Check for SRS columns and add them if MIGRATE_SRS is enabled.
    Columns added: next_review INTEGER, interval INTEGER DEFAULT 0, efactor REAL DEFAULT 2.5, repetitions INTEGER DEFAULT 0
    This function will not remove or modify existing columns.
    """
    cols = _get_table_columns(conn, 'words')
    required = {
        'next_review': "next_review INTEGER",
        'interval': "interval INTEGER DEFAULT 0",
        'efactor': "efactor REAL DEFAULT 2.5",
        'repetitions': "repetitions INTEGER DEFAULT 0",
    }
    missing = [k for k in required.keys() if k not in cols]
    if not missing:
        return

    msg = f"SRS columns missing: {missing}. MIGRATE_SRS={'1' if MIGRATE_SRS else '0'}"
    logging.info(msg)
    if not MIGRATE_SRS:
        logging.info("Auto-migration disabled; set MIGRATE_SRS=1 to add SRS columns automatically or run tools/migrate_add_srs.py")
        return

    # Backup DB file (best-effort)
    try:
        ts = int(time.time())
        backup = f"{DB_NAME}.bak.{ts}"
        import shutil

        shutil.copyfile(DB_NAME, backup)
        logging.info("Database backed up to %s before migration", backup)
    except Exception:
        logging.exception("Failed to create DB backup before migration; proceeding with caution")

    # Add missing columns
    for k in missing:
        try:
            _add_column(conn, 'words', required[k])
            logging.info("Added column %s", k)
        except Exception:
            logging.exception("Failed to add column %s", k)


def _fetch_word_by_id(conn, word_id):
    cur = conn.cursor()
    cur.execute("SELECT * FROM words WHERE id = ?", (word_id,))
    row = cur.fetchone()
    return row


def schedule_review(conn, word_id, quality):
    """Schedule/update SRS fields for a word using SM-2-inspired rules.
    quality: int 0-5 (5 best)
    Returns updated row as dict.
    """
    if quality is None:
        raise ValueError("quality required")
    quality = int(quality)
    if quality < 0 or quality > 5:
        raise ValueError("quality must be 0-5")

    now = int(time.time())
    cur = conn.cursor()
    row = _fetch_word_by_id(conn, word_id)
    if not row:
        return None

    # Read existing SRS values, provide defaults if missing
    efactor = float(row['efactor'] or 2.5) if 'efactor' in row.keys() else 2.5
    interval = int(row['interval'] or 0) if 'interval' in row.keys() else 0
    repetitions = int(row['repetitions'] or 0) if 'repetitions' in row.keys() else 0

    # SM-2 algorithm (standard): adjust efactor and intervals
    if quality < 3:
        # repeat next day, reset repetitions
        repetitions = 0
        interval = 1
    else:
        repetitions += 1
        if repetitions == 1:
            interval = 1
        elif repetitions == 2:
            interval = 6
        else:
            # multiply previous interval by efactor
            interval = max(1, round(interval * efactor))

    # Update efactor based on quality
    # Standard SM-2 efactor update formula
    # ef' = ef + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
    efactor = efactor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    if efactor < 1.3:
        efactor = 1.3

    next_review = now + interval * 86400

    cur.execute("""
        UPDATE words
        SET efactor = ?, interval = ?, repetitions = ?, next_review = ?
        WHERE id = ?
    """, (efactor, interval, repetitions, next_review, word_id))

    conn.commit()
    # Clear cached statistics if needed
    try:
        clear_statistics_cache()
    except Exception:
        pass

    cur.execute("SELECT * FROM words WHERE id = ?", (word_id,))
    return dict(cur.fetchone())


# ------------------ App teardown ------------------
@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop('db', None)
    if db is not None:
        try:
            db.close()
        except Exception:
            pass


# ------------------ Pagination helper ------------------
def parse_pagination_args():
    try:
        page = int(request.args.get('page', 1))
        if page < 1:
            page = 1
    except ValueError:
        page = 1
    try:
        limit = int(request.args.get('limit', 50))
        # Enforce sensible bounds to avoid huge payloads
        if limit < 1:
            limit = 50
        if limit > 500:
            limit = 500
    except ValueError:
        limit = 50
    offset = (page - 1) * limit
    return page, limit, offset


# ------------------ CSRF & Auth helpers ------------------

def ensure_csrf_token():
    """Ensure a CSRF token exists in session and return it."""
    token = session.get('csrf_token')
    if not token:
        token = secrets.token_urlsafe(32)
        session['csrf_token'] = token
    return token


def _is_valid_csrf(req):
    # Header-based check
    header = req.headers.get('X-CSRF-Token')
    if header and session.get('csrf_token') and header == session.get('csrf_token'):
        return True
    return False


def _is_valid_api_token(req):
    # Read API token from environment at call-time so tests and runtime can set it dynamically
    api_token = os.environ.get('API_TOKEN')
    auth = req.headers.get('Authorization', '')
    if auth.startswith('Bearer '):
        token = auth.split(' ', 1)[1].strip()
        if api_token and token == api_token:
            return True
    return False


def require_auth(f):
    """Decorator for mutating endpoints. Accepts either a valid API token (Bearer)
    or a valid X-CSRF-Token header that matches the session token.
    If neither present the request is rejected.
    """
    @wraps(f)
    def wrapped(*args, **kwargs):
        # If API token present and valid, allow
        if _is_valid_api_token(request):
            return f(*args, **kwargs)
        # Otherwise, require valid CSRF token for browser-originated requests
        if _is_valid_csrf(request):
            return f(*args, **kwargs)
        # Not authorized
        return jsonify({'success': False, 'message': 'Missing or invalid authentication/CSRF token'}), 401
    return wrapped


# ------------------ Simple cache helpers ------------------
@lru_cache(maxsize=1)
def _cached_statistics():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 總單字數
    cursor.execute("SELECT COUNT(*) as count FROM words")
    total_words = cursor.fetchone()['count']

    # 資料夾數
    cursor.execute("SELECT COUNT(DISTINCT folder) as count FROM words")
    total_folders = cursor.fetchone()['count']

    # 錯誤單字數
    cursor.execute("SELECT COUNT(*) as count FROM words WHERE error_count > 0")
    words_with_errors = cursor.fetchone()['count']

    # 總錯誤次數
    cursor.execute("SELECT SUM(error_count) as total FROM words")
    total_errors = cursor.fetchone()['total'] or 0

    # 各資料夾統計
    cursor.execute("""
        SELECT folder, COUNT(*) as count
        FROM words
        GROUP BY folder
        ORDER BY folder
    """)

    folder_stats = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return {
        'total_words': total_words,
        'total_folders': total_folders,
        'words_with_errors': words_with_errors,
        'total_errors': total_errors,
        'folder_stats': folder_stats
    }


def clear_statistics_cache():
    try:
        _cached_statistics.cache_clear()
    except Exception:
        pass


# ------------------ Routes ------------------
@app.before_request
def ensure_session_csrf():
    # Ensure session has csrf token for browser flows
    ensure_csrf_token()


@app.route('/')
def index():
    """首頁"""
    return render_template('vocabmaster.html', csrf_token=session.get('csrf_token'))


@app.route('/api/words', methods=['GET'])
def get_words():
    """取得單字，支援分頁與搜尋（使用 FTS5 優先，否則使用 LIKE 回退）。

    Query params:
      - folder: string (optional, 'all' means no folder filter)
      - page: int
      - limit: int
      - keyword: string (search term)
    """
    folder = request.args.get('folder')
    keyword = (request.args.get('keyword') or '').strip()
    page, limit, offset = parse_pagination_args()

    # Validate keyword length
    if keyword and (len(keyword) < 1 or len(keyword) > 200):
        # Return empty result set for out-of-range keyword
        resp = jsonify({'page': page, 'limit': limit, 'total': 0, 'words': []})
        resp.headers['Cache-Control'] = 'public, max-age=30'
        return resp

    conn = get_db()
    cursor = conn.cursor()

    where_clauses = []
    params = []
    if folder and folder != 'all':
        where_clauses.append('folder = ?')
        params.append(folder)

    total = 0
    # If a keyword is provided, prefer using FTS if available
    if keyword:
        # Check for words_fts
        try:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='words_fts'")
            fts_exists = cursor.fetchone() is not None
        except Exception:
            fts_exists = False

        if fts_exists:
            # Use FTS MATCH query and compute total via COUNT on joined table
            match_expr = keyword
            where_clause = ' AND '.join(where_clauses) if where_clauses else '1=1'
            count_sql = f"SELECT COUNT(*) as cnt FROM words w JOIN words_fts f ON f.rowid = w.id WHERE {where_clause} AND words_fts MATCH ?"
            count_params = params + [match_expr]
            cursor.execute(count_sql, tuple(count_params))
            total = cursor.fetchone()['cnt']

            data_sql = f"SELECT w.id, w.english, w.chinese, w.folder, w.error_count, w.created_at FROM words w JOIN words_fts f ON f.rowid = w.id WHERE {where_clause} AND words_fts MATCH ? ORDER BY w.folder, w.english LIMIT ? OFFSET ?"
            data_params = params + [match_expr, limit, offset]
            cursor.execute(data_sql, tuple(data_params))
            words = [dict(row) for row in cursor.fetchall()]

            resp = jsonify({'page': page, 'limit': limit, 'total': total, 'words': words})
            resp.headers['Cache-Control'] = 'public, max-age=30'
            return resp
        else:
            # Fallback to LIKE
            search_pattern = f"%{keyword}%"
            where_clauses.append('(english LIKE ? OR chinese LIKE ?)')
            params.extend([search_pattern, search_pattern])

    # Build final where clause
    where_clause = ('WHERE ' + ' AND '.join(where_clauses)) if where_clauses else ''

    # Count total
    count_sql = f"SELECT COUNT(*) as cnt FROM words {where_clause}"
    cursor.execute(count_sql, tuple(params))
    total = cursor.fetchone()['cnt']

    # Select only necessary columns
    data_sql = f"SELECT id, english, chinese, folder, error_count, created_at FROM words {where_clause} ORDER BY folder, english LIMIT ? OFFSET ?"
    data_params = params + [limit, offset]
    cursor.execute(data_sql, tuple(data_params))
    words = [dict(row) for row in cursor.fetchall()]

    resp = jsonify({'page': page, 'limit': limit, 'total': total, 'words': words})
    resp.headers['Cache-Control'] = 'public, max-age=30'
    return resp


@app.route('/api/words', methods=['POST'])
@require_auth
def add_word():
    """新增單字（簡單 validation + 參數長度限制）"""
    data = request.get_json(silent=True) or {}
    english = (data.get('english') or '').strip().lower()
    chinese = (data.get('chinese') or '').strip()
    folder = (data.get('folder') or '').strip().lower()

    # 基本驗證與長度上限
    if not english or not chinese or not folder:
        return jsonify({'success': False, 'message': '所有欄位都必須填寫'}), 400
    if len(english) > 200 or len(chinese) > 500 or len(folder) > 100:
        return jsonify({'success': False, 'message': '欄位長度超過限制'}), 400

    conn = get_db()
    cursor = conn.cursor()

    # 檢查是否已存在
    cursor.execute("""
        SELECT id FROM words WHERE folder = ? AND english = ?
    """, (folder, english))

    if cursor.fetchone():
        return jsonify({'success': False, 'message': '單字已存在'}), 400

    # 新增單字
    cursor.execute("""
        INSERT INTO words (english, chinese, folder, error_count)
        VALUES (?, ?, ?, 0)
    """, (english, chinese, folder))

    conn.commit()
    word_id = cursor.lastrowid
    clear_statistics_cache()

    return jsonify({
        'success': True,
        'message': '新增成功',
        'id': word_id
    }), 201


@app.route('/api/words/<int:word_id>', methods=['DELETE'])
@require_auth
def delete_word(word_id):
    """刪除單字"""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM words WHERE id = ?", (word_id,))

    conn.commit()
    clear_statistics_cache()

    return jsonify({'success': True, 'message': '刪除成功'})


@app.route('/api/words/<int:word_id>/error', methods=['PUT'])
@require_auth
def update_error_count(word_id):
    """更新錯誤次數（基本驗證）"""
    data = request.get_json(silent=True) or {}
    try:
        error_count = int(data.get('error_count', 0))
    except (TypeError, ValueError):
        return jsonify({'success': False, 'message': 'error_count 必須為整數'}), 400

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE words SET error_count = ? WHERE id = ?
    """, (error_count, word_id))

    conn.commit()
    clear_statistics_cache()

    return jsonify({'success': True})


@app.route('/api/folders', methods=['GET'])
def get_folders():
    """取得所有資料夾"""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT DISTINCT folder FROM words ORDER BY folder
    """)

    folders = [row['folder'] for row in cursor.fetchall()]

    resp = jsonify(folders)
    # Short client cache for folders
    resp.headers['Cache-Control'] = 'public, max-age=30'
    return resp


@app.route('/api/search', methods=['GET'])
def search_words():
    """搜尋單字（若資料量大，會優先使用 FTS5，若不可用則回退到 LIKE）"""
    keyword = request.args.get('keyword', '').strip()

    if not keyword:
        return jsonify([])

    # 防止過短或過長查詢
    if len(keyword) < 1 or len(keyword) > 200:
        return jsonify([])

    conn = get_db()
    cursor = conn.cursor()

    # 檢查是否存在 words_fts 這個 virtual table
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='words_fts'")
    fts_exists = cursor.fetchone() is not None

    if fts_exists:
        # Use FTS5 MATCH safely with parameters
        try:
            match_expr = keyword
            cursor.execute("SELECT w.* FROM words w JOIN words_fts f ON f.rowid = w.id WHERE words_fts MATCH ? LIMIT 100", (match_expr,))
            words = [dict(row) for row in cursor.fetchall()]
            return jsonify(words)
        except sqlite3.OperationalError:
            # Fall back to LIKE if any issue
            pass

    # Fallback to parameterized LIKE query
    search_pattern = f"%{keyword}%"
    cursor.execute("""
        SELECT * FROM words
        WHERE english LIKE ? OR chinese LIKE ?
        ORDER BY folder, english
        LIMIT 100
    """, (search_pattern, search_pattern))

    words = [dict(row) for row in cursor.fetchall()]

    return jsonify(words)


@app.route('/api/errors', methods=['GET'])
def get_error_words():
    """取得錯題"""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM words
        WHERE error_count > 0
        ORDER BY error_count DESC, english
        LIMIT 500
    """)

    words = [dict(row) for row in cursor.fetchall()]

    return jsonify(words)


@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    """取得統計資訊（使用簡單快取）"""
    stats = _cached_statistics()
    return jsonify(stats)


# ------------------ SRS API endpoints ------------------
@app.route('/api/due', methods=['GET'])
def get_due_words():
    """Return words due for review: next_review IS NULL OR next_review <= now. Supports pagination and folder filter."""
    folder = request.args.get('folder')
    page, limit, offset = parse_pagination_args()
    now = int(time.time())

    conn = get_db()
    cursor = conn.cursor()

    where_clauses = ["(next_review IS NULL OR next_review <= ?) "]
    params = [now]
    if folder and folder != 'all':
        where_clauses.append('folder = ?')
        params.append(folder)

    where_clause = 'WHERE ' + ' AND '.join(where_clauses)

    count_sql = f"SELECT COUNT(*) as cnt FROM words {where_clause}"
    cursor.execute(count_sql, tuple(params))
    total = cursor.fetchone()['cnt']

    data_sql = f"SELECT id, english, chinese, folder, error_count, created_at, next_review, interval, efactor, repetitions FROM words {where_clause} ORDER BY next_review ASC, folder, english LIMIT ? OFFSET ?"
    data_params = params + [limit, offset]
    cursor.execute(data_sql, tuple(data_params))
    words = [dict(row) for row in cursor.fetchall()]

    resp = jsonify({'page': page, 'limit': limit, 'total': total, 'words': words})
    resp.headers['Cache-Control'] = 'public, max-age=15'
    return resp


@app.route('/api/words/<int:word_id>/review', methods=['PUT'])
@require_auth
def review_word(word_id):
    """Record a review for a single word. Accepts JSON {quality: 0-5} and returns updated word row."""
    data = request.get_json(silent=True) or {}
    q = data.get('quality')
    try:
        quality = int(q)
    except Exception:
        return jsonify({'success': False, 'message': 'quality must be an integer 0-5'}), 400
    if quality < 0 or quality > 5:
        return jsonify({'success': False, 'message': 'quality must be between 0 and 5'}), 400

    conn = get_db()
    updated = schedule_review(conn, word_id, quality)
    if not updated:
        return jsonify({'success': False, 'message': 'word not found'}), 404
    return jsonify({'success': True, 'word': updated})


# ------------------ Export / Import (CSV) endpoints ------------------
@app.route('/api/export', methods=['GET'])
def export_csv():
    """Simple CSV export of all words. Returns text/csv."""
    import csv
    from io import StringIO

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, english, chinese, folder, error_count, created_at, next_review, interval, efactor, repetitions FROM words ORDER BY folder, english")
    rows = cur.fetchall()

    si = StringIO()
    writer = csv.writer(si)
    writer.writerow(['id','english','chinese','folder','error_count','created_at','next_review','interval','efactor','repetitions'])
    for r in rows:
        writer.writerow([r['id'], r['english'], r['chinese'], r['folder'], r['error_count'], r['created_at'], r.get('next_review'), r.get('interval'), r.get('efactor'), r.get('repetitions')])

    output = si.getvalue()
    from flask import Response
    resp = Response(output, mimetype='text/csv')
    resp.headers['Content-Disposition'] = 'attachment; filename=words_export.csv'
    return resp


@app.route('/api/import', methods=['POST'])
@require_auth
def import_csv():
    """Import CSV (multipart form file upload) into database. Dedupe by folder+english."""
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'no file uploaded'}), 400
    f = request.files['file']
    import csv
    from io import StringIO

    data = f.read().decode('utf-8')
    si = StringIO(data)
    reader = csv.DictReader(si)
    conn = get_db()
    cur = conn.cursor()
    added = 0
    for row in reader:
        english = (row.get('english') or '').strip().lower()
        chinese = (row.get('chinese') or '').strip()
        folder = (row.get('folder') or '').strip().lower() or 'imported'
        if not english or not chinese:
            continue
        # dedupe
        cur.execute("SELECT id FROM words WHERE folder = ? AND english = ?", (folder, english))
        if cur.fetchone():
            continue
        cur.execute("INSERT INTO words (english, chinese, folder, error_count) VALUES (?, ?, ?, 0)", (english, chinese, folder))
        added += 1
    conn.commit()
    clear_statistics_cache()
    return jsonify({'success': True, 'added': added})


if __name__ == '__main__':
    # 初始化資料庫（在 app context 中執行）
    with app.app_context():
        init_db()

    # 啟動伺服器
    print("🚀 伺服器啟動中...")
    print("📱 請開啟瀏覽器訪問: http://localhost:5000")

    # Do not enable debug in production. Control via FLASK_ENV or use a WSGI server like gunicorn.
    app.run(host='0.0.0.0', port=5000)
