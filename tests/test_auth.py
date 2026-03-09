import os
import json
import tempfile
from web import app


def setup_test_db(tmp_path):
    db_file = tmp_path / "test_vocab.db"
    os.environ['DB_NAME'] = str(db_file)
    with app.app_context():
        # initialize schema using web.init_db
        from web import init_db
        init_db()
    return str(db_file)


def test_register_and_login(tmp_path):
    db = setup_test_db(tmp_path)
    app.config['TESTING'] = True
    client = app.test_client()

    # register
    resp = client.post('/auth/register', json={'email': 'test@example.com', 'password': 'pass'})
    assert resp.status_code == 200
    j = resp.get_json()
    assert j.get('success') is True
    user_id = j.get('id')
    assert isinstance(user_id, int)

    # logout then login
    client.post('/auth/logout')
    resp = client.post('/auth/login', json={'email': 'test@example.com', 'password': 'pass'})
    assert resp.status_code == 200
    j = resp.get_json()
    assert j.get('success') is True
    assert 'id' in j

    # me endpoint
    resp = client.get('/auth/me')
    assert resp.status_code == 200
    j = resp.get_json()
    assert j.get('success') is True
    assert j.get('user') is not None
