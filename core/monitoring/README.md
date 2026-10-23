<!--
SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
SPDX-License-Identifier: Apache-2.0
-->

# Giám sát (profile `monitoring`, #78)

`make demo` bật profile này cùng `integration`. Grafana mở tại
http://127.0.0.1:3001 (đổi bằng `GRAFANA_PORT`), tài khoản `GRAFANA_ADMIN_USER` /
`GRAFANA_ADMIN_PASSWORD` trong `.env`. Dashboard "DX-Lab: tổng quan vận hành" là
trang chủ. Chỉ Grafana mở cổng, và chỉ trên `127.0.0.1`; Prometheus và mọi endpoint
metric nằm trong mạng Docker.

| Service | Image | Vai trò |
|---|---|---|
| prometheus | `prom/prometheus:v3.15.0` | Thu metric mỗi 15 giây, giữ 7 ngày (`prometheus.yml`) |
| grafana | `grafana/grafana:13.2.4` | Dashboard nạp qua provisioning; không đăng ký, không ẩn danh, không gửi số liệu sử dụng ra ngoài |
| postgres-exporter | `prometheuscommunity/postgres-exporter:v0.20.1` | Thống kê PostgreSQL bằng role `dxmonitor` (`pg_monitor`), không dùng tài khoản superuser |
| nats-exporter | `natsio/prometheus-nats-exporter:0.20.2` | Metric NATS và JetStream từ cổng monitoring 8222 |

| Nguồn | Endpoint trong mạng Docker | Ghi chú |
|---|---|---|
| APISIX | `apisix:9091/apisix/prometheus/metrics` | Plugin `prometheus` qua `global_rules`, áp cho mọi route |
| Keycloak | `keycloak:9000/metrics` | `KC_METRICS_ENABLED=true` |
| PostgreSQL | `postgres-exporter:9187` | |
| Data API | `data-api:9100` | Độ trễ theo route, bước quy trình theo `action` và `co_so`, kết quả bàn giao cập nhật tài sản |
| asset-sync | `asset-sync:9100` | Cập nhật Snipe-IT theo kết quả, sự kiện NATS theo cách xử lý |
| NATS | `nats-exporter:7777` | |

Route `/api/data` của gateway trỏ vào cổng 8000 của Data API, nên `/api/data/metrics`
qua gateway không lộ metric.

**Flowable.** Đã kiểm tra image `flowable/flowable-rest:7.2.0`: `/flowable-rest/actuator`
và `/actuator/metrics` trả 200 (JSON của Micrometer), còn `/actuator/prometheus` trả
404 vì image không kèm registry Prometheus. Thêm registry đòi build lại image Flowable,
nên Prometheus không thu Flowable. Số liệu quy trình lấy từ Data API
(`dxlab_ticket_transitions_total`); Flowable sống hay chết thấy ở healthcheck Compose.

Máy đã có volume PostgreSQL từ trước #78 thì script tạo `dxmonitor` không chạy lại.
Tạo một lần bằng `make psql` rồi:

```sql
CREATE ROLE dxmonitor LOGIN PASSWORD '<MONITOR_DB_PASSWORD trong .env>';
GRANT pg_monitor TO dxmonitor;
```

Kiểm tra: `make demo`, `make smoke` (để gateway và Data API có số liệu), rồi
`make smoke-monitoring`. Script đi qua API của Grafana: dashboard đã nạp, các target
lõi đang lên, có số request gateway, `pg_up`, số liệu của cả 3 database và số bước
quy trình.

Dashboard nằm ở `grafana/dashboards/dxlab-overview.json`; sửa trên giao diện không
được lưu (`allowUiUpdates: false`), muốn đổi thì sửa tệp JSON.
