# SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
# SPDX-License-Identifier: Apache-2.0
FROM python:3.12.12-slim-bookworm
WORKDIR /service
COPY ai/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY ai/app.py ai/rules.py ai/model.py ai/train.py ./
COPY data/samples/training_data.jsonl ./training_data.jsonl
RUN python train.py --data training_data.jsonl --output model.joblib \
    && useradd --uid 10001 --create-home dxai \
    && chown -R dxai:dxai /service
USER dxai
EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
