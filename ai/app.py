# SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
# SPDX-License-Identifier: Apache-2.0

"""Classifier API; model errors and timeouts fall back to local keyword rules."""

import os
from concurrent.futures import ThreadPoolExecutor, TimeoutError

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from rules import classify as classify_rules


app = FastAPI(title="DX-Lab Intelligence", version="0.1.0")
workers = ThreadPoolExecutor(max_workers=2, thread_name_prefix="classifier")


class Text(BaseModel):
    title: str = Field(default="", max_length=200)
    description: str = Field(min_length=1, max_length=10000)


def predict_model(title: str, description: str) -> dict:
    # model.py and its artifact arrive in #28; absence is an expected fallback.
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
    except (ImportError, OSError, ValueError, TimeoutError):
        suggestion = classify_rules(body.title, body.description)
        if suggestion is None:
            raise HTTPException(422, "No matching keyword; select category manually") from None
        return suggestion
