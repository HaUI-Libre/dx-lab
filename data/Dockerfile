# SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
# SPDX-License-Identifier: Apache-2.0
FROM python:3.12.12-slim-bookworm
WORKDIR /service
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py migrate.py schema.sql ./
COPY migrations ./migrations
RUN useradd --uid 10001 --create-home dxdata && chown -R dxdata:dxdata /service
USER dxdata
EXPOSE 8000
CMD ["sh", "-c", "python migrate.py && exec uvicorn app:app --host 0.0.0.0 --port 8000"]
