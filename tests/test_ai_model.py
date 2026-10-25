# SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
# SPDX-License-Identifier: Apache-2.0

"""Train on the labeled samples and check model output without committing artifacts."""

import sys
from pathlib import Path

import pytest

pytest.importorskip("sklearn")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "ai"))
from train import train  # noqa: E402
import model  # noqa: E402


def test_training_and_prediction(tmp_path, monkeypatch):
    source = Path(__file__).resolve().parents[1] / "data/samples/training_data.jsonl"
    artifact = tmp_path / "model.joblib"
    metrics = train(source, artifact)
    assert metrics["train_samples"] + metrics["test_samples"] == 160
    assert metrics["category"]["accuracy"] >= 0.7
    assert metrics["priority"]["macro_f1"] >= 0.4
    assert len(metrics["category"]["confusion_matrix"]) == 4
    monkeypatch.setenv("AI_MODEL_PATH", str(artifact))
    model.bundle.cache_clear()
    result = model.predict("Máy chiếu phòng thi bốc khói trước buổi thi")
    assert result["category"] == "HARDWARE"
    assert result["priority"] == "URGENT"
    assert result["keywords"]
    assert 0 <= result["confidence"] <= 1
