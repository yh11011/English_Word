"""歷屆生字：共用既有 words 與 SRS，不另建學習資料庫。"""
import json
import time
from functools import wraps
from pathlib import Path

from flask import Blueprint, current_app, jsonify, render_template, request

FOLDER = '歷屆英文'
DEFAULT_BANK = Path(__file__).parent / 'data/exam_vocabulary.json'


def register_exam_vocabulary(app, get_db, get_current_user, ensure_csrf_token,
                             valid_csrf, jwt_auth, schedule_review, clear_cache):
    bp = Blueprint('exam_vocabulary', __name__)

    def bank():
        path = Path(current_app.config.get('EXAM_VOCABULARY_BANK', DEFAULT_BANK))
        return json.loads(path.read_text(encoding='utf-8'))

    def authenticated(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            user = get_current_user()
            if not user:
                return jsonify({'error': '請先回單字首頁登入，再開啟歷屆生字。'}), 401
            if request.method != 'GET' and not (valid_csrf(request) or (jwt_auth is not None and jwt_auth(request) is not None)):
                return jsonify({'error': '頁面已失效，請重新整理後再試。'}), 401
            return f(user, *args, **kwargs)
        return wrapped

    @bp.get('/exam-vocabulary')
    def page():
        return render_template('exam_vocabulary.html', csrf_token=ensure_csrf_token())

    @bp.get('/api/exam-vocabulary')
    @authenticated
    def candidates(user):
        data = bank()
        rows = get_db().execute('SELECT id,english FROM words WHERE owner_id=? AND folder=?',
                                (user['id'], FOLDER)).fetchall()
        return jsonify({**data, 'saved': {r['english']: r['id'] for r in rows}})

    @bp.post('/api/exam-vocabulary/save')
    @authenticated
    def save(user):
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict) or not isinstance(payload.get('word'), str):
            return jsonify({'error': '請選擇清單中的單字。'}), 400
        item = next((i for i in bank()['items'] if i['word'] == payload['word']), None)
        if item is None:
            return jsonify({'error': '找不到這個候選字。'}), 404
        conn = get_db()
        # 序列化檢查與寫入，重複點擊不建立多份學習進度。
        conn.execute('BEGIN IMMEDIATE')
        try:
            row = conn.execute('SELECT id FROM words WHERE owner_id=? AND folder=? AND english=?',
                               (user['id'], FOLDER, item['word'])).fetchone()
            if row:
                word_id = row['id']
            else:
                cur = conn.execute('INSERT INTO words (english,chinese,folder,owner_id) VALUES (?,?,?,?)',
                                   (item['word'], item['meaning'], FOLDER, user['id']))
                word_id = cur.lastrowid
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        clear_cache()
        return jsonify({'id': word_id, 'word': item['word'], 'created': row is None})

    @bp.get('/api/exam-vocabulary/due')
    @authenticated
    def due(user):
        rows = get_db().execute('''SELECT id,english,chinese FROM words
            WHERE owner_id=? AND folder=? AND (next_review IS NULL OR next_review<=?)
            ORDER BY next_review,id LIMIT 20''', (user['id'], FOLDER, int(time.time()))).fetchall()
        return jsonify({'words': [dict(r) for r in rows]})

    @bp.post('/api/exam-vocabulary/review')
    @authenticated
    def review(user):
        data = request.get_json(silent=True)
        if (not isinstance(data, dict) or type(data.get('id')) is not int
                or type(data.get('quality')) is not int or data['quality'] not in (1, 3, 5)):
            return jsonify({'error': '請選擇不記得、吃力或記得。'}), 400
        conn = get_db()
        row = conn.execute('SELECT id FROM words WHERE id=? AND owner_id=? AND folder=?',
                           (data['id'], user['id'], FOLDER)).fetchone()
        if row is None:
            return jsonify({'error': '找不到這筆學習紀錄。'}), 404
        updated = schedule_review(conn, row['id'], data['quality'])
        return jsonify({'success': True, 'next_review': updated['next_review']})

    @bp.after_request
    def no_cache(response):
        response.headers['Cache-Control'] = 'no-store'
        return response

    app.register_blueprint(bp)
