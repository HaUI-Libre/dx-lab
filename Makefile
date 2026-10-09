# SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
# SPDX-License-Identifier: Apache-2.0

.PHONY: help env up down logs ps check-spdx check

help:            ## Hiển thị danh sách lệnh
	@grep -E '^[a-zA-Z_-]+:.*## ' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*## "}{printf "  %-12s %s\n",$$1,$$2}'

env:             ## Tạo .env từ .env.example nếu chưa có
	@test -f .env || cp .env.example .env && echo ".env đã sẵn sàng, nhớ đổi các giá trị changeme"

up: env          ## Khởi động toàn bộ hệ thống
	docker compose up -d

down:            ## Dừng hệ thống
	docker compose down

logs:            ## Xem log
	docker compose logs -f --tail=100

ps:              ## Trạng thái các service
	docker compose ps

check-spdx:      ## Kiểm tra SPDX header
	./scripts/check_spdx.sh

check: check-spdx ## Chạy các kiểm tra cục bộ
