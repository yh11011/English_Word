import sqlite3


def test_get_words_empty(client):
    resp = client.get('/api/words')
    assert resp.status_code == 200
    assert resp.get_json()['words'] == []
    assert resp.get_json()['total'] == 0


def test_add_and_delete_word_with_token(client, monkeypatch):
    monkeypatch.setenv('API_TOKEN', 'test-token')
    headers = {'Authorization': 'Bearer test-token'}
    payload = {'english': 'banana', 'chinese': '香蕉', 'folder': 'fruits'}
    resp = client.post('/api/words', json=payload, headers=headers)
    assert resp.status_code == 201
    word_id = resp.get_json()['id']
    assert client.get('/api/words').get_json()['words'][0]['id'] == word_id

    resp = client.delete(f'/api/words/{word_id}', headers=headers)
    assert resp.status_code == 200
    assert resp.get_json()['success'] is True
    assert client.get('/api/words').get_json()['total'] == 0


def test_csrf_protection_for_mutation(client):
    resp = client.post('/api/words', json={
        'english': 'pear', 'chinese': '梨', 'folder': 'fruits',
    })
    assert resp.status_code == 401
    assert client.get('/api/words').get_json()['total'] == 0


def test_database_uses_temporary_path(isolated_app, tmp_path):
    from web import get_db

    with isolated_app.app_context():
        connection = get_db()
        assert connection.execute('PRAGMA database_list').fetchone()['file'] == str(tmp_path / 'test_vocab.db')
        assert get_db() is connection
    # 請求環境結束後必須釋放連線。
    import pytest
    with pytest.raises(sqlite3.ProgrammingError):
        connection.execute('SELECT 1')
