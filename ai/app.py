# SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
# SPDX-License-Identifier: Apache-2.0

"""Classifier API; model errors and timeouts fall back to local keyword rules."""

import os
from concurrent.futures import ThreadPoolExecutor
from importlib import metadata

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from rules import classify as classify_rules

# Image Docker cài bằng requirements.txt, không có metadata gói; giữ khớp pyproject.toml
# (tests/test_ai_http.py kiểm tra)
FALLBACK_VERSION = "1.0.1"
try:
    VERSION = metadata.version("dxlab-ai-classifier")
except metadata.PackageNotFoundError:
    VERSION = FALLBACK_VERSION

app = FastAPI(title="DX-Lab Intelligence", version=VERSION)
workers = ThreadPoolExecutor(max_workers=2, thread_name_prefix="classifier")


class Text(BaseModel):
    title: str = Field(default="", max_length=200)
    description: str = Field(min_length=1, max_length=10000)


def predict_model(title: str, description: str) -> dict:
    # Imported per call: a missing model.py or artifact is an expected fallback to rules
    from model import predict  # pylint: disable=import-outside-toplevel
    return predict(f"{title} {description}")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/classify")
def classify(body: Text):
    try:
        timeout = max(0.01, float(os.getenv("AI_MODEL_TIMEOUT_SECONDS", "1")))
        result = workers.submit(predict_model, body.title, body.description).result(timeout)
        return {**result, "source": "model"}
    except Exception:  # A broken model must never remove the rule-based suggestion.
        suggestion = classify_rules(body.title, body.description)
        if suggestion is None:
            raise HTTPException(422, "No matching keyword; select category manually") from None
        return suggestion
