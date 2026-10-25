# SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
# SPDX-License-Identifier: Apache-2.0

"""Fallback suggestions remain available without a model or when it times out."""

import sys
import importlib.util
from concurrent.futures import TimeoutError
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "ai"))
spec = importlib.util.spec_from_file_location(
    "ai_service_app", Path(__file__).resolve().parents[1] / "ai" / "app.py")
ai_app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ai_app)
from rules import classify as classify_rules  # noqa: E402


def test_keyword_explanation_and_priority():
    result = classify_rules("Máy chiếu bốc khói", "Buổi thi bắt đầu ngay")
    assert result["category"] == "HARDWARE"
    assert result["priority"] == "URGENT"
    assert "máy chiếu" in result["keywords"]
    assert "buổi thi" in result["keywords"]


def test_no_match_does_not_invent_category():
    assert classify_rules("Sự cố", "Cần kiểm tra thêm") is None


@pytest.mark.parametrize("failure", [ImportError("model absent"), TimeoutError()])
def test_api_falls_back_when_model_fails(monkeypatch, failure):
    def fail(*_):
        raise failure
    monkeypatch.setattr(ai_app, "predict_model", fail)
    result = ai_app.classify(ai_app.Text(title="Mất mạng LAN", description="Cả phòng mất kết nối"))
    assert result["source"] == "rules"
    assert result["category"] == "NETWORK_ACCOUNT"
    assert result["priority"] == "HIGH"


def test_api_reports_model_source(monkeypatch):
    monkeypatch.setattr(ai_app, "predict_model", lambda *_: {
        "category": "HARDWARE", "priority": "MEDIUM", "keywords": ["máy chiếu"]})
    result = ai_app.classify(ai_app.Text(title="Máy chiếu", description="Hỏng bóng đèn"))
    assert result["source"] == "model"
