#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
# SPDX-License-Identifier: Apache-2.0
"""Issue #78: Grafana has the dashboard and Prometheus holds real gateway and database data.

Run after `make demo` and `make smoke` (so the gateway has traffic): `make smoke-monitoring`.
Goes through Grafana's datasource proxy, the only monitoring port open on the host.
"""

import base64
import json
import os
import sys
import time
import urllib.parse
import urllib.request

GRAFANA = f"http://127.0.0.1:{os.getenv('GRAFANA_PORT', '3001')}"
AUTH = base64.b64encode(f"{os.getenv('GRAFANA_ADMIN_USER', 'admin')}:"
                        f"{os.environ['GRAFANA_ADMIN_PASSWORD'].strip()}".encode()).decode()
CORE_JOBS = ("prometheus", "apisix", "keycloak", "postgres", "data-api")
INTEGRATION_JOBS = ("asset-sync", "nats")
failed = 0


def get(path):
    request = urllib.request.Request(GRAFANA + path, headers={"Authorization": f"Basic {AUTH}"})
    with urllib.request.urlopen(request, timeout=15) as r:
        return json.load(r)


def query(expr):
    path = "/api/datasources/proxy/uid/prometheus/api/v1/query?" + urllib.parse.urlencode({"query": expr})
    return get(path)["data"]["result"]


def check(ok, desc):
    global failed
    print(f"{'OK  ' if ok else 'FAIL'}  monitoring: {desc}")
    failed += not ok


check(get("/api/health").get("database") == "ok", "Grafana chạy")
dashboard = get("/api/dashboards/uid/dxlab-overview")["dashboard"]
check(len(dashboard["panels"]) >= 10, f"dashboard \"{dashboard['title']}\" nạp từ provisioning")

# Lần scrape đầu cần vài chu kỳ 15 giây sau khi stack vừa lên
deadline = time.monotonic() + 90
while True:
    up = {item["metric"]["job"]: item["value"][1] for item in query("up")}
    if all(up.get(job) == "1" for job in CORE_JOBS) or time.monotonic() > deadline:
        break
    time.sleep(5)
for job in CORE_JOBS:
    check(up.get(job) == "1", f"target {job} đang lên")
for job in INTEGRATION_JOBS:
    state = {"1": "lên", "0": "xuống (profile integration tắt?)"}.get(up.get(job), "chưa có")
    print(f"INFO  monitoring: target {job} {state}")

requests = sum(float(item["value"][1]) for item in query("sum(apisix_http_status)"))
check(requests > 0, f"gateway có số liệu thật ({requests:.0f} request đã đếm)")
check(any(item["value"][1] == "1" for item in query("pg_up")), "PostgreSQL có số liệu qua postgres_exporter")
databases = {item["metric"].get("datname") for item in query("pg_stat_activity_count")}
check({"dxdata", "keycloak", "flowable"} <= databases, "thấy cả 3 database dxdata, keycloak, flowable")
transitions = query("sum(dxlab_ticket_transitions_total)")
check(bool(transitions) and float(transitions[0]["value"][1]) > 0,
      "Data API có đếm bước quy trình (cần chạy make smoke trước)")

sys.exit(1 if failed else 0)
