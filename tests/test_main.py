import datetime

import pytest
from fastapi.testclient import TestClient

import main
from audit import AuditModelError, AuditReport

client = TestClient(main.app)


def _ok_report(text: str) -> AuditReport:
    """Двойник audit(): не ходит в сеть, возвращает валидный отчёт."""
    return AuditReport(errors=[], summary="ok")


def _post(content: bytes = b"hello world", name: str = "a.txt", ctype: str = "text/plain", **kw):
    return client.post("/audit", files={"file": (name, content, ctype)}, **kw)


@pytest.fixture(autouse=True)
def _reset(monkeypatch):
    """Сбрасывает общее состояние лимитов и ставит щедрые дефолты, чтобы тесты
    не влияли друг на друга. Конкретные тесты переопределяют нужный лимит."""
    main._hits.clear()
    main._daily["day"] = datetime.date.today()
    main._daily["count"] = 0
    monkeypatch.setattr(main, "RATE_LIMIT", 1000)
    monkeypatch.setattr(main, "DAILY_CAP", 1000)
    monkeypatch.setattr(main, "MAX_INPUT_CHARS", 50000)
    monkeypatch.setattr(main, "AUDIT_API_KEY", "")  # демо открыто по умолчанию
    yield


def test_happy_path(monkeypatch):
    monkeypatch.setattr(main, "audit", _ok_report)
    resp = _post()
    assert resp.status_code == 200
    assert resp.json() == {"errors": [], "summary": "ok"}


def test_empty_file_is_400():
    assert _post(content=b"").status_code == 400


def test_unsupported_format_is_400():
    assert _post(name="a.pdf", ctype="application/pdf").status_code == 400


def test_blank_text_is_400():
    assert _post(content=b"   \n  ").status_code == 400


def test_oversized_input_is_413(monkeypatch):
    monkeypatch.setattr(main, "MAX_INPUT_CHARS", 5)
    monkeypatch.setattr(main, "audit", _ok_report)
    assert _post(content=b"way too long for the cap").status_code == 413


def test_per_ip_rate_limit_is_429(monkeypatch):
    monkeypatch.setattr(main, "RATE_LIMIT", 1)
    monkeypatch.setattr(main, "audit", _ok_report)
    assert _post().status_code == 200
    assert _post().status_code == 429


def test_daily_cap_is_429(monkeypatch):
    monkeypatch.setattr(main, "DAILY_CAP", 1)
    monkeypatch.setattr(main, "audit", _ok_report)
    assert _post().status_code == 200
    assert _post().status_code == 429


def test_optional_key_enforced_when_set(monkeypatch):
    monkeypatch.setattr(main, "AUDIT_API_KEY", "secret")
    monkeypatch.setattr(main, "audit", _ok_report)
    assert _post().status_code == 401
    assert _post(headers={"X-API-Key": "wrong"}).status_code == 401
    assert _post(headers={"X-API-Key": "secret"}).status_code == 200


def test_model_error_maps_to_502(monkeypatch):
    def _boom(text: str) -> AuditReport:
        raise AuditModelError("no tool_use")

    monkeypatch.setattr(main, "audit", _boom)
    assert _post().status_code == 502
