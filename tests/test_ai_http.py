# SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
# SPDX-License-Identifier: Apache-2.0

"""Exercise the classifier through HTTP, including validation and fallbacks."""

import importlib.util
import sys
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


AI_DIR = Path(__file__).resolve().parents[1] / "ai"
sys.path.insert(0, str(AI_DIR))
spec = importlib.util.spec_from_file_location("ai_http_app", AI_DIR / "app.py")
ai_app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ai_app)
from rules import CATEGORIES, PRIORITIES  # noqa: E402

client = TestClient(ai_app.app)
VALID = {"title": "Mất mạng LAN", "description": "Cả phòng mất kết nối"}


def assert_suggestion(response, source):
    assert response.status_code == 200
    body = response.json()
    assert {"category", "priority", "keywords", "source"} <= body.keys()
    assert body["category"] in CATEGORIES
    assert body["priority"] in (*PRIORITIES, "MEDIUM")
    assert body["source"] == source
    assert isinstance(body["keywords"], list)
    assert all(isinstance(word, str) and word for word in body["keywords"])
    return body


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_openapi_version_matches_pyproject():
    # Phiên bản không còn ghi cứng 0.1.0; bản chạy từ image dùng FALLBACK_VERSION (#139)
    import tomllib
    declared = tomllib.loads((AI_DIR / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]
    assert ai_app.FALLBACK_VERSION == declared
    assert client.get("/openapi.json").json()["info"]["version"] == ai_app.VERSION


def test_model_response_shape(monkeypatch):
    monkeypatch.setattr(ai_app, "predict_model", lambda *_: {
        "category": "NETWORK_ACCOUNT", "priority": "HIGH", "keywords": ["mất mạng"]})
    assert_suggestion(client.post("/classify", json=VALID), "model")


@pytest.mark.parametrize("body", [
    {"title": "A", "description": ""},
    {"title": "A", "description": "x" * 10001},
    {"title": "x" * 201, "description": "Mất mạng"},
])
def test_invalid_input_is_422(body):
    assert client.post("/classify", json=body).status_code == 422


def test_rule_fallback_and_no_match(monkeypatch):
    monkeypatch.setattr(ai_app, "predict_model", lambda *_: (_ for _ in ()).throw(
        RuntimeError("model unavailable")))
    suggestion = assert_suggestion(client.post("/classify", json=VALID), "rules")
    assert suggestion["category"] == "NETWORK_ACCOUNT"
    no_match = client.post("/classify", json={"title": "Sự cố", "description": "Cần kiểm tra thêm"})
    assert no_match.status_code == 422
    assert "select category manually" in no_match.json()["detail"]


def test_real_timeout_returns_rules_promptly(monkeypatch):
    monkeypatch.setenv("AI_MODEL_TIMEOUT_SECONDS", "0.02")
    def slow_model(*_):
        time.sleep(0.5)
        return {"category": "HARDWARE", "priority": "LOW", "keywords": []}
    monkeypatch.setattr(ai_app, "predict_model", slow_model)
    started = time.monotonic()
    suggestion = assert_suggestion(client.post("/classify", json=VALID), "rules")
    assert time.monotonic() - started < 0.35
    assert suggestion["category"] == "NETWORK_ACCOUNT"
