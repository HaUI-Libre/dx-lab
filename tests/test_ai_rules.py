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


# Câu lấy từ data/samples/training_data.jsonl, luật trước #138 trả None hoặc sai loại
@pytest.mark.parametrize("title, description, keyword", [
    ("Loa ngoài phòng thực hành tiếng Anh bị rè", "Phát âm thanh rè rè rất khó nghe", "loa"),
    ("Webcam phòng học trực tuyến hình ảnh mờ", "Ống kính không bắt nét khuôn mặt", "webcam"),
    ("Cổng tai nghe 3.5mm bị gãy chân tiếp xúc", "Chỉ nghe được một bên tai", "tai nghe"),
    ("Quạt thông gió phòng máy kêu cót két", "Thỉnh thoảng phát tiếng kêu", "quạt"),
    ("Cáp HDMI phòng H2-205 bị đứt ngầm", "Mất tín hiệu khi xê dịch dây", "hdmi"),
    # Không dấu vẫn khớp vì rules.fold() bỏ dấu trước khi so
    ("Loa phong may bi re", "Am thanh nho", "loa"),
])
def test_peripheral_keywords_are_hardware(title, description, keyword):
    result = classify_rules(title, description)
    assert result["category"] == "HARDWARE"
    assert keyword in result["keywords"]


def test_ups_beats_server_room_wording():
    # Mẫu 3 của dữ liệu huấn luyện: "máy chủ" từng kéo phiếu sang NETWORK_ACCOUNT
    result = classify_rules("Sập hệ thống cấp điện UPS phòng máy chủ",
                            "Bộ lưu điện cảnh báo pin quá nhiệt")
    assert result["category"] == "HARDWARE"
    assert {"ups", "bộ lưu điện"} <= set(result["keywords"])


@pytest.mark.parametrize("failure", [ImportError("model absent"), TimeoutError(),
                                     RuntimeError("model inference failed")])
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
