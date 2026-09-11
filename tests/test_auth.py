from unittest.mock import Mock

import pytest
import requests
import web


@pytest.fixture
def auth_server(monkeypatch):
    post = Mock(return_value=Mock(status_code=200, json=Mock(return_value={
        'access_token': 'mock-auth-token',
        'user': {'id': 42, 'email': 'test@example.com', 'display_name': '測試使用者'},
    })))
    monkeypatch.setattr(web.http_requests, 'post', post)
    return post


def test_register_and_login(client, auth_server):
    payload = {'username_or_email': 'test@example.com', 'password': 'test-password'}
    for action in ('register', 'login'):
        resp = client.post(f'/auth/{action}', json=payload)
        assert resp.status_code == 200
        assert resp.get_json() == {'success': True, 'id': 42, 'access_token': 'mock-auth-token'}
        auth_server.assert_called_with(f'{web.AUTH_SERVICE_URL}/{action}', json=payload, timeout=10)
        user = client.get('/auth/me').get_json()['user']
        assert user['id'] == 42
        assert user['email'] == 'test@example.com'
        assert 'password_hash' not in user
        assert client.post('/auth/logout').status_code == 200
        assert client.get('/auth/me').get_json()['user'] is None


@pytest.mark.parametrize('action', ['register', 'login'])
def test_auth_missing_credentials(client, auth_server, action):
    assert client.post(f'/auth/{action}', json={}).status_code == 400
    auth_server.assert_not_called()


@pytest.mark.parametrize('action,status', [('register', 409), ('login', 401)])
def test_auth_rejection_does_not_create_session(client, auth_server, action, status):
    auth_server.return_value.status_code = status
    resp = client.post(f'/auth/{action}', json={'username': 'test', 'password': 'wrong'})
    assert resp.status_code == status
    assert client.get('/auth/me').get_json()['user'] is None


@pytest.mark.parametrize('action', ['register', 'login'])
def test_auth_service_unavailable(client, auth_server, action):
    auth_server.side_effect = requests.ConnectionError('offline')
    resp = client.post(f'/auth/{action}', json={'username': 'test', 'password': 'test-password'})
    assert resp.status_code == 503
    assert client.get('/auth/me').get_json()['user'] is None
