import os
import json
import tempfile
import sqlite3
from web import app


def setup_test_db(tmp_path):
    db_file = tmp_path / "test_vocab.db"
    # Ensure the app uses this DB
    os.environ['DB_NAME'] = str(db_file)
    # Initialize DB
    with app.app_context():
        from migrate_to_sqlite import create_database
        create_database(str(db_file))
    return str(db_file)


def test_get_words_empty(tmp_path):
    db = setup_test_db(tmp_path)
    app.config['TESTING'] = True
    client = app.test_client()
    resp = client.get('/api/words')
    assert resp.status_code == 200
    data = resp.get_json()
    assert 'words' in data


def test_add_and_delete_word_with_token(tmp_path, monkeypatch):
    db = setup_test_db(tmp_path)
    app.config['TESTING'] = True
    client = app.test_client()
    # Set API_TOKEN for this process
    monkeypatch.setenv('API_TOKEN', 'test-token')
    # Need to reload web module's API_TOKEN — since tests import web already, set header directly
    headers = {'Authorization': 'Bearer test-token', 'Content-Type': 'application/json'}
    payload = {'english': 'banana', 'chinese': '香蕉', 'folder': 'fruits'}
    resp = client.post('/api/words', data=json.dumps(payload), headers=headers)
    assert resp.status_code in (200, 201)
    j = resp.get_json()
    assert j.get('success') is True
    word_id = j.get('id')
    assert isinstance(word_id, int)

    # Delete
    resp = client.delete(f'/api/words/{word_id}', headers=headers)
    assert resp.status_code == 200
    j = resp.get_json()
    assert j.get('success') is True


def test_csrf_protection_for_mutation(tmp_path):
    db = setup_test_db(tmp_path)
    app.config['TESTING'] = True
    client = app.test_client()
    # Attempt to add word without token or CSRF -> should be 401
    payload = {'english': 'pear', 'chinese': '梨', 'folder': 'fruits'}
    resp = client.post('/api/words', json=payload)
    assert resp.status_code == 401
