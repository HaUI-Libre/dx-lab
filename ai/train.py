# SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
# SPDX-License-Identifier: Apache-2.0

"""Train reproducible text classifiers and evaluate on a held-out split."""

import argparse
import hashlib
import json
from pathlib import Path

import joblib
import sklearn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline


def train(data_path: Path, output_path: Path) -> dict:
    raw = data_path.read_bytes()
    rows = [json.loads(line) for line in raw.splitlines() if line.strip()]
    texts = [f"{row['title']} {row['description']}" for row in rows]
    categories = [row["category"] for row in rows]
    priorities = [row["priority"] for row in rows]
    # Keep every category/priority combination in the test set; no sample is fitted twice.
    indices = list(range(len(rows)))
    train_ids, test_ids = train_test_split(
        indices, test_size=0.25, random_state=42,
        stratify=[f"{c}:{p}" for c, p in zip(categories, priorities)])
    trained = {}
    metrics = {}
    for name, labels in (("category", categories), ("priority", priorities)):
        model = make_pipeline(
            TfidfVectorizer(ngram_range=(1, 2), min_df=1, sublinear_tf=True),
            LogisticRegression(max_iter=2000, class_weight="balanced", random_state=42))
        model.fit([texts[i] for i in train_ids], [labels[i] for i in train_ids])
        expected = [labels[i] for i in test_ids]
        predicted = model.predict([texts[i] for i in test_ids])
        names = sorted(set(labels))
        metrics[name] = {
            "accuracy": round(float(accuracy_score(expected, predicted)), 4),
            "macro_f1": round(float(f1_score(expected, predicted, average="macro")), 4),
            "labels": names,
            "confusion_matrix": confusion_matrix(expected, predicted, labels=names).tolist(),
        }
        trained[name] = model
    output_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"models": trained, "sklearn_version": sklearn.__version__,
                 "data_sha256": hashlib.sha256(raw).hexdigest()}, output_path)
    return {"samples": len(rows), "train_samples": len(train_ids),
            "test_samples": len(test_ids), "random_state": 42,
            "data_sha256": hashlib.sha256(raw).hexdigest(), "sklearn_version": sklearn.__version__,
            **metrics}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, default=Path(__file__).resolve().parent / "training_data.jsonl")
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parent / "model.joblib")
    options = parser.parse_args()
    print(json.dumps(train(options.data, options.output), ensure_ascii=False, indent=2))
