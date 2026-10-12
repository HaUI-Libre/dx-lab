# SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
# SPDX-License-Identifier: Apache-2.0

.PHONY: help env up down logs ps psql smoke check-spdx check

help:            ## Hiển thị danh sách lệnh
	@grep -E '^[a-zA-Z_-]+:.*## ' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*## "}{printf "  %-12s %s\n",$$1,$$2}'

env:             ## Tạo .env từ .env.example nếu chưa có
	@if [ ! -f .env ]; then cp .env.example .env; echo "Đã tạo .env, đổi các giá trị changeme trước khi chạy"; fi

up: env          ## Khởi động toàn bộ hệ thống
	docker compose up -d --wait

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

check-spdx:      ## Kiểm tra SPDX header
	./scripts/check_spdx.sh

check: check-spdx ## Chạy các kiểm tra cục bộ
