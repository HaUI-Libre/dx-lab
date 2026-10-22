# SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
# SPDX-License-Identifier: Apache-2.0

.PHONY: help env up down logs ps psql smoke seed lint-license check

help:            ## Hiển thị danh sách lệnh
	@grep -E '^[a-zA-Z_-]+:.*## ' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*## "}{printf "  %-12s %s\n",$$1,$$2}'

env:             ## Tạo .env từ .env.example với khoá ngẫu nhiên nếu chưa có
	@./scripts/init-env.sh

up: env          ## Khởi động toàn bộ hệ thống
	@if grep -q '^DATA_WORKFLOW_KEY=changeme$$' .env; then \
	  echo "DATA_WORKFLOW_KEY trong .env vẫn là changeme, Data API sẽ không gọi được Flowable."; \
	  echo "Đặt một chuỗi ngẫu nhiên dài, ví dụ: openssl rand -hex 24"; exit 1; fi
	docker compose up -d --wait --scale workflow-deploy=0
	docker compose run --build --rm --no-deps workflow-deploy

down:            ## Dừng hệ thống
	docker compose down

logs:            ## Xem log
	docker compose logs -f --tail=100

ps:              ## Trạng thái các service
	docker compose ps

psql:            ## Mở psql vào PostgreSQL (DB=<tên> để chọn database)
	docker compose exec postgres sh -c 'psql -U "$$POSTGRES_USER" -d "$(or $(DB),$$POSTGRES_DB)"'

smoke:           ## Kiểm tra gateway: 401 / 200 / 403
	./scripts/smoke.sh

seed:            ## Nạp dữ liệu mẫu vào PostgreSQL
	python3 scripts/seed.py

lint-license:    ## Kiểm tra giấy phép từng tệp theo chuẩn REUSE (cần cài reuse)
	reuse lint

check: lint-license ## Chạy các kiểm tra cục bộ
