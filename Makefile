# SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
# SPDX-License-Identifier: Apache-2.0

.PHONY: help env env-check up demo down logs ps psql smoke smoke-assets smoke-monitoring seed test lint-license check

# Mọi profile ngoài mặc định; down và ps liệt kê để dừng, xem cả service của chúng
ALL_PROFILES := --profile integration --profile monitoring --profile setup

help:            ## Hiển thị danh sách lệnh
	@grep -E '^[a-zA-Z_-]+:.*## ' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*## "}{printf "  %-12s %s\n",$$1,$$2}'

env:             ## Tạo .env từ .env.example với khoá ngẫu nhiên nếu chưa có
	@./scripts/init-env.sh

env-check: env
	@if grep -q '^DATA_WORKFLOW_KEY=changeme$$' .env; then \
	  echo "DATA_WORKFLOW_KEY trong .env vẫn là changeme, Data API sẽ không gọi được Flowable."; \
	  echo "Đặt một chuỗi ngẫu nhiên dài, ví dụ: openssl rand -hex 24"; exit 1; fi

up: env-check    ## Khởi động profile mặc định (lõi và dịch vụ của đội)
	docker compose up -d --wait
	docker compose run --build --rm --no-deps workflow-deploy

demo: env-check  ## Khởi động mọi profile (thêm integration, monitoring) cho buổi demo
	docker compose --profile integration --profile monitoring up -d --wait
	docker compose run --build --rm --no-deps workflow-deploy

down:            ## Dừng hệ thống, kể cả service của các profile
	docker compose $(ALL_PROFILES) down

logs:            ## Xem log
	docker compose logs -f --tail=100

ps:              ## Trạng thái các service
	docker compose $(ALL_PROFILES) ps

psql:            ## Mở psql vào PostgreSQL (DB=<tên> để chọn database)
	docker compose exec postgres sh -c 'psql -U "$$POSTGRES_USER" -d "$(or $(DB),$$POSTGRES_DB)"'

smoke:           ## Kiểm tra gateway: 401 / 200 / 403
	./scripts/smoke.sh

smoke-assets:    ## Kiểm tra Snipe-IT qua gateway (cần profile integration)
	@set -a; . ./.env; set +a; python3 scripts/test-assets-api.py

smoke-monitoring: ## Kiểm tra Grafana, Prometheus có số liệu thật (cần profile monitoring)
	@set -a; . ./.env; set +a; python3 scripts/test-monitoring.py

seed:            ## Nạp dữ liệu mẫu vào PostgreSQL
	python3 scripts/seed.py

test:            ## Chạy test Python trong tests/ (cần data/requirements.txt và pytest)
	DATA_DB_PASSWORD=unused-in-tests python3 -m pytest -q tests/

snipeit-token:   ## Hiển thị API token của Snipe-IT
	@docker compose --profile integration exec snipeit cat /token/snipeit_api_token 2>/dev/null || echo "Chưa có token. Hãy khởi động Snipe-IT trước."

lint-license:    ## Kiểm tra giấy phép từng tệp theo chuẩn REUSE (cần cài reuse)
	reuse lint

check: lint-license ## Chạy các kiểm tra cục bộ

