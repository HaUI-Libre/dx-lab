# SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
# SPDX-License-Identifier: Apache-2.0
FROM python:3.12.12-slim-bookworm
WORKDIR /service
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py adapter.py ./
RUN useradd --uid 10001 --gid 0 --create-home asset-sync && mkdir /state && chown asset-sync:root /state
USER asset-sync
EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
