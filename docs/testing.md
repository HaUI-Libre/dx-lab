<!--
SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
SPDX-License-Identifier: Apache-2.0
-->

# Kiểm thử (#33)

Ba lớp: test Python không cần stack, smoke test trên stack thật, và CI dựng stack từ
máy sạch. Mọi lệnh chạy từ thư mục gốc repo.

## 1. Test Python (`make test`)

`pytest` trên `tests/`, dùng giả lập, không cần Docker. CI job `Python tests`.

| Tệp | Kiểm tra |
|---|---|
| `tests/test_data_api.py` | Xác thực token (chữ ký, `iss`, `azp`, vai trò), quyền theo vai trò và `co_so`, chuyển trạng thái và task Flowable |
| `tests/test_data_stats.py` | `GET /stats`: trưởng phòng chỉ cơ sở trong token, hỏi cơ sở khác 403, admin mọi cơ sở hoặc một cơ sở, vai trò khác 403, lọc thời gian, không tính bản nháp (#22) |
| `tests/test_data_provenance.py` | Provenance, lịch sử sự kiện, `reopen_count`, đánh giá |
| `tests/test_asset_sync.py` | Adapter Snipe-IT với Snipe-IT giả lập: tra thiết bị, lưu và trả nhãn, thử lại |
| `tests/test_asset_events.py` | Sự kiện NATS: chọn sự kiện, ack/nak/term, Data API quay về lời gọi trực tiếp khi bus lỗi hoặc treo |
| `tests/test_workflow_deploy.py` | Deploy BPMN chỉ khi nội dung đổi |
| `tests/test_ai_rules.py` | Dịch vụ phân loại: luật từ khoá có giải thích, không khớp thì không tự đặt loại, API quay về luật khi mô hình thiếu, lỗi hoặc quá thời gian, báo đúng nguồn `model` (#30, #31) |
| `tests/test_ai_model.py` | Huấn luyện từ `data/samples/training_data.jsonl` rồi dự đoán (#28); bỏ qua khi máy không có scikit-learn, CI job `AI classifier` có |
| `tests/test_ai_http.py` | `TestClient` gọi `/health` và `/classify`: đầu vào sai, phản hồi mô hình/luật, 422 khi không khớp, fallback khi suy luận thật sự quá thời gian (#142) |
| `tests/test_ai_quality.py` | Chia 120/40 mẫu theo seed 42 và cặp nhãn; ghi lại đầu vào `fit`, bảo đảm không chứa mẫu giữ lại; accuracy loại sự cố ≥ 0,80 trên 40 mẫu chưa huấn luyện (#142). Bỏ qua nếu không có scikit-learn; CI `AI classifier` có thư viện này |

## 2. Smoke test trên stack thật

| Lệnh | Cần | Kiểm tra |
|---|---|---|
| `make smoke` | `make up` | Token và `co_so` của 10 tài khoản; gateway 401/403/200; quyền tệp theo thư mục và chặn `..`, `%2e`; service account Keycloak chỉ đọc; vòng đời ticket qua Data API (giao sai cơ sở, thiếu biên bản, mở lại, từ chối); tệp đính kèm; đăng nhập qua app; trang ticket và thống kê render đúng nút theo vai trò; `GET /api/data/stats` khớp đếm thẳng trên PostgreSQL theo cơ sở (#22); portal |
| `scripts/test-workflow-api.sh` | `make up` | Ba nhánh BPMN `success`, `reject`, `reopen` trên Flowable qua gateway |
| `make smoke-assets` | `make demo` | Thiết bị từ Snipe-IT theo người, mã, phòng; nhãn "Đang sửa chữa" rồi trả nhãn cũ; đóng ticket lúc `asset-sync` dừng, bật lại vẫn cập nhật |
| `make smoke-monitoring` | `make demo`, `make smoke` | Dashboard Grafana, target đang lên, số liệu thật của gateway và database |
| `make test-e2e` | `make demo` | Chuỗi demo qua gateway (SSO, Snipe-IT, ảnh, định tuyến, phân công, nhãn qua NATS, mở lại, nghiệm thu, đánh giá, provenance) và nhánh từ chối, không asset_id, phân loại không phản hồi (#34). Bước phụ thuộc phần chưa có in `[SKIP]`, không tính là đạt |

`make smoke` đạt cả khi profile `integration` bật và tắt.

## 3. CI

| Job | Khi nào | Nội dung |
|---|---|---|
| `REUSE lint` | Mọi PR, push `main` | Giấy phép từng tệp |
| `Secret scan (gitleaks)` | Mọi PR, push `main` | Toàn bộ lịch sử git |
| `PR title (Conventional Commits)` | Mọi PR | Tiêu đề PR thành tiêu đề commit khi squash |
| `Python tests` | Mọi PR, push `main` | Mục 1 |
| `Stack từ volume trống (make up, make smoke)` | PR chạm `core/`, `data/`, `app/`, `scripts/`, `tests/`, `docker-compose.yml`, `.env.example`, `Makefile`; push `main` | `make env`, `docker compose build`, `make up`, `make seed`, `make smoke`, `scripts/test-workflow-api.sh` trên runner sạch: bằng chứng build from source |
| `asset-flow` | PR chạm phần tích hợp tài sản | Dựng lõi và profile `integration`, `make smoke-assets` |
| `AI classifier` | PR chạm `ai/`, `data/samples/training_data.jsonl`, `tests/test_ai_*.py`; push `main` | Cài `ai/requirements.txt` và HTTPX cho TestClient, chạy mọi `tests/test_ai_*.py`, huấn luyện lại mô hình từ dữ liệu mẫu |
| `App Nuxt (build, chạy ngoài repo)` | PR chạm `app/`, `data/`, `ai/`, `core/gateway/plugins/`, `scripts/test-lua-plugin.sh`, `Makefile` hoặc workflow; push `main` | Theo [build-from-source.md](build-from-source.md) mục 1: `npm ci`, `npm run build`, chép `.output` ra `$RUNNER_TEMP`, xoá `.output` và `node_modules` trong repo, chạy bằng Node, `/healthz` 200, route cần đăng nhập trả 401, `PORTAL_DATA_DIR` đọc được |
| `Plugin dxlab-roles (cài vào APISIX riêng)` | Như dòng trên | `make test-lua`: chép plugin vào APISIX dựng riêng, token tự ký, 401/403/200 |
| `Data API (pip install, chạy ngoài repo)` | Như dòng trên | Theo [build-from-source.md](build-from-source.md) mục 3: venv sạch, `pip install ./data`, chạy `dxlab-data-api` ngoài `$RUNNER_TEMP`, `/health` 200 không cần PostgreSQL |
| `Dịch vụ phân loại (pip install, huấn luyện, chạy ngoài repo)` | Như dòng trên | `pip install ./ai`, huấn luyện bằng `dxlab-ai-train` ra `$RUNNER_TEMP`, chạy `dxlab-ai-classifier`, `/health` và `/classify` với câu khớp luật dự phòng đều 200 |

Năm job đầu là required check của ruleset `main`.

## Còn thiếu

- Thao tác trên trình duyệt (bấm nút, chọn ảnh, gợi ý phân loại hiện ra, cập nhật trực
  tiếp): chưa có test tự động; kiểm tra tay theo `docs/manual-checks.md`, biên bản ở
  `docs/demo/bien-ban-di-vong-trinh-duyet.md` (#26).
