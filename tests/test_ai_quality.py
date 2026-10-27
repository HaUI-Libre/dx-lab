# SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
# SPDX-License-Identifier: Apache-2.0

"""Guard held-out category quality and verify the training set stays separate."""

import json
import sys
from pathlib import Path

import pytest

pytest.importorskip("sklearn")
from sklearn.feature_extraction.text import TfidfVectorizer  # noqa: E402
from sklearn.model_selection import train_test_split  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ai"))
from train import train  # noqa: E402


def test_category_accuracy_on_unseen_samples(tmp_path, monkeypatch):
    source = ROOT / "data/samples/training_data.jsonl"
    rows = [json.loads(line) for line in source.read_text().splitlines() if line.strip()]
    texts = [f"{row['title']} {row['description']}" for row in rows]
    indices = list(range(len(rows)))
    train_ids, test_ids = train_test_split(
        indices, test_size=0.25, random_state=42,
        stratify=[f"{row['category']}:{row['priority']}" for row in rows])
    training_texts = [texts[i] for i in train_ids]
    held_out_texts = {texts[i] for i in test_ids}
    assert len(train_ids) == 120 and len(test_ids) == 40
    assert not (set(training_texts) & held_out_texts)

    fitted_inputs = []
    original_fit_transform = TfidfVectorizer.fit_transform
    def record_fit(self, raw_documents, y=None, **fit_params):
        documents = list(raw_documents)
        fitted_inputs.append(documents)
        return original_fit_transform(self, documents, y=y, **fit_params)
    monkeypatch.setattr(TfidfVectorizer, "fit_transform", record_fit)

    metrics = train(source, tmp_path / "held-out-model.joblib")
    assert len(fitted_inputs) == 2  # category and priority models
    assert all(documents == training_texts for documents in fitted_inputs)
    assert all(not (set(documents) & held_out_texts) for documents in fitted_inputs)
    assert metrics["train_samples"] == 120 and metrics["test_samples"] == 40
    # The small, team-written corpus previously scored 0.90; 0.80 allows modest
    # edits while still catching a large regression on genuinely unseen rows.
    assert metrics["category"]["accuracy"] >= 0.80
