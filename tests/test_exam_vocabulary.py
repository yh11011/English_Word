import json
import sqlite3
import time
from pathlib import Path

import pytest
import web
from tools.build_exam_vocabulary import build


@pytest.fixture
def learner(client, isolated_app, tmp_path, monkeypatch):
    path = tmp_path / 'bank.json'
    path.write_text(json.dumps({'audit': {'documents': 1}, 'items': [
        {'word': 'decision', 'meaning': '決定', 'level': 2, 'exam_count': 2, 'sources': []},
        {'word': 'careful', 'meaning': '小心的', 'level': 1, 'exam_count': 1, 'sources': []},
    ]}))
    monkeypatch.setitem(isolated_app.config, 'EXAM_VOCABULARY_BANK', path)
    with isolated_app.app_context():
        db = web.get_db()
        db.execute('INSERT INTO users (id) VALUES (42)')
        db.execute('INSERT INTO users (id) VALUES (43)')
        db.commit()
    with client.session_transaction() as session:
        session['user_id'] = 42
        session['csrf_token'] = 'test-csrf'
    return client, {'X-CSRF-Token': 'test-csrf'}


def test_private_candidates_and_csrf(client, learner):
    c, headers = learner
    assert c.get('/api/exam-vocabulary').status_code == 200
    assert c.post('/api/exam-vocabulary/save', json={'word': 'decision'}).status_code == 401
    with c.session_transaction() as session:
        session.clear()
    for endpoint in ('', '/due'):
        response = c.get('/api/exam-vocabulary' + endpoint)
        assert response.status_code == 401
        assert response.headers['Cache-Control'] == 'no-store'
    assert c.post('/api/exam-vocabulary/save', json={'word': 'decision'}, headers=headers).status_code == 401
    assert c.get('/exam-vocabulary').status_code == 200


def test_save_review_and_user_isolation(learner):
    c, headers = learner
    first = c.post('/api/exam-vocabulary/save', json={'word': 'decision'}, headers=headers).get_json()
    assert first['created'] is True
    repeated = c.post('/api/exam-vocabulary/save', json={'word': 'decision'}, headers=headers).get_json()
    assert repeated == {**first, 'created': False}
    assert c.get('/api/exam-vocabulary/due').get_json()['words'][0]['english'] == 'decision'
    response = c.post('/api/exam-vocabulary/review', json={'id': first['id'], 'quality': 5}, headers=headers)
    assert response.status_code == 200
    assert response.get_json()['next_review'] > time.time()
    assert c.get('/api/exam-vocabulary/due').get_json()['words'] == []
    c.post('/api/exam-vocabulary/save', json={'word': 'decision'}, headers=headers)
    assert c.get('/api/exam-vocabulary/due').get_json()['words'] == []
    with c.session_transaction() as session:
        session['user_id'] = 43
    assert c.get('/api/exam-vocabulary').get_json()['saved'] == {}
    assert c.post('/api/exam-vocabulary/review', json={'id': first['id'], 'quality': 1}, headers=headers).status_code == 404
    second = c.post('/api/exam-vocabulary/save', json={'word': 'decision'}, headers=headers).get_json()
    assert second['id'] != first['id']


@pytest.mark.parametrize('payload', [None, [], {}, {'word': 123}])
def test_save_invalid_payload(learner, payload):
    c, headers = learner
    assert c.post('/api/exam-vocabulary/save', json=payload, headers=headers).status_code == 400


def test_unknown_word_and_invalid_score(learner):
    c, headers = learner
    assert c.post('/api/exam-vocabulary/save', json={'word': 'invented'}, headers=headers).status_code == 404
    for payload in ([], {'id': True, 'quality': 5}, {'id': 1, 'quality': 4}, {'id': 1, 'quality': '5'}):
        assert c.post('/api/exam-vocabulary/review', json=payload, headers=headers).status_code == 400


def test_interval_days_schema(learner, isolated_app):
    c, headers = learner
    with isolated_app.app_context():
        db = web.get_db()
        db.execute('ALTER TABLE words RENAME COLUMN interval TO interval_days')
        db.commit()
    word = c.post('/api/exam-vocabulary/save', json={'word': 'careful'}, headers=headers).get_json()
    assert c.post('/api/exam-vocabulary/review', json={'id': word['id'], 'quality': 1}, headers=headers).status_code == 200


def test_build_excludes_metadata_and_counts_distinct_exams(tmp_path):
    database = tmp_path / 'dictionary.db'
    with sqlite3.connect(database) as conn:
        conn.execute('CREATE TABLE words (id INTEGER,english TEXT,chinese TEXT,folder TEXT)')
        conn.executemany('INSERT INTO words VALUES (?,?,?,?)', [
            (1,'decision','決定','第二級'), (2,'secret','秘密','第一級'), (3,'careful','小心','第一級')])
    source = tmp_path / 'source'
    for name in ('exam1/a.md', 'exam1/b.md', 'exam2/c.md'):
        p = source / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text('# secret\n\n## 題目內容\n\nA decision is a decision.\n\n---\n\n## 答案\nsecret careful\n')
    result = build(source, database)
    assert len(result['items']) == 1
    assert result['items'][0]['word'] == 'decision'
    assert result['items'][0]['exam_count'] == 2
    assert result['items'][0]['question_count'] == 3
    assert result == build(source, database)
