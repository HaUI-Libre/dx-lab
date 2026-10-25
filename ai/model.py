# SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
# SPDX-License-Identifier: Apache-2.0

"""Load the model built from the team's data and explain active text features."""

import os
from functools import lru_cache

import joblib


@lru_cache(maxsize=1)
def bundle():
    return joblib.load(os.getenv("AI_MODEL_PATH", "/service/model.joblib"))


def evidence(model, text: str, predicted: str) -> list[str]:
    vectorizer, classifier = model.steps[0][1], model.steps[1][1]
    vector = vectorizer.transform([text])
    class_index = list(classifier.classes_).index(predicted)
    features = vectorizer.get_feature_names_out()
    ranked = sorted(((classifier.coef_[class_index, index] * value, features[index])
                     for index, value in zip(vector.indices, vector.data)
                     if classifier.coef_[class_index, index] > 0), reverse=True)
    return [feature for _, feature in ranked[:3]]


def predict(text: str) -> dict:
    models = bundle()["models"]
    category = str(models["category"].predict([text])[0])
    priority = str(models["priority"].predict([text])[0])
    keywords = list(dict.fromkeys(evidence(models["category"], text, category) +
                                  evidence(models["priority"], text, priority)))
    confidence = min(models["category"].predict_proba([text])[0].max(),
                     models["priority"].predict_proba([text])[0].max())
    return {"category": category, "priority": priority,
            "keywords": keywords, "confidence": round(float(confidence), 4)}
