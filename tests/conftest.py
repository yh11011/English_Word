"""共用測試環境：隔離資料庫、工作目錄、快取與外部 HTTP。"""
import sys
from pathlib import Path

import pytest
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


@pytest.fixture(autouse=True)
def isolated_app(tmp_path, monkeypatch):
    import web

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv('DB_NAME', str(tmp_path / 'test_vocab.db'))
    monkeypatch.delenv('API_TOKEN', raising=False)
    monkeypatch.setattr(web, 'DB_NAME', str(tmp_path / 'test_vocab.db'))
    monkeypatch.setattr(web, 'MIGRATE_SRS', False)
    monkeypatch.setitem(web.app.config, 'TESTING', True)
    monkeypatch.setitem(web.app.config, 'SECRET_KEY', 'isolated-test-session-key')
    monkeypatch.setattr(web.ai_service, 'db_path', str(tmp_path / 'test_vocab.db'))

    def block_http(*args, **kwargs):
        raise AssertionError('測試必須模擬外部 HTTP，不能呼叫真實服務')

    monkeypatch.setattr(requests.sessions.Session, 'request', block_http)
    web.clear_statistics_cache()
    with web.app.app_context():
        web.init_db()
    yield web.app
    web.clear_statistics_cache()


@pytest.fixture
def client(isolated_app):
    return isolated_app.test_client()
