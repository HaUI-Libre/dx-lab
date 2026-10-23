#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
# SPDX-License-Identifier: Apache-2.0
#
# Kiểm tra các trang ticket của app (#26) bằng phiên đăng nhập thật: trang render ở
# server đúng nút cho từng vai trò và trạng thái. Các bước chuyển trạng thái gọi qua
# /gw/api/data như giao diện. Tạo ticket mới mỗi lần chạy.

set -euo pipefail

cd "$(dirname "$0")/.."
set -a
# shellcheck disable=SC1091
. ./.env
set +a
DEMO_USER_PASSWORD=$(printf '%s' "$DEMO_USER_PASSWORD" | tr -d '\r')

APP="http://localhost:${APP_PORT:-3000}"
failed=0
jars=()
trap 'rm -f "${jars[@]}"' EXIT

login() {
  local jar kc_url form back
  jar=$(mktemp); jars+=("$jar")
  kc_url=$(curl -s -c "$jar" -o /dev/null -w '%{redirect_url}' "$APP/auth/login")
  form=$(curl -s -b "$jar" -c "$jar" "$kc_url" | grep -o 'action="[^"]*"' | head -n 1 | sed 's/^action="//; s/"$//; s/&amp;/\&/g')
  back=$(curl -s -b "$jar" -c "$jar" -o /dev/null -w '%{redirect_url}' -X POST "$form" \
    --data-urlencode "username=$1" --data-urlencode "password=$DEMO_USER_PASSWORD")
  curl -s -b "$jar" -c "$jar" -o /dev/null "$back"
  printf '%s' "$jar"
}

# page <jar> <path> <mô tả> <chuỗi phải có>...
page() {
  local jar="$1" path="$2" desc="$3"; shift 3
  local body code missing=()
  body=$(curl -s -b "$jar" -w '\n%{http_code}' "$APP$path")
  code=${body##*$'\n'}
  for text in "$@"; do
    [[ "$body" == *"$text"* ]] || missing+=("$text")
  done
  if [ "$code" = 200 ] && [ ${#missing[@]} -eq 0 ]; then
    echo "OK    200  app $desc"
  else
    echo "FAIL  $code  app $desc (thiếu: ${missing[*]:-})"
    failed=$((failed + 1))
  fi
}

# absent <jar> <path> <mô tả> <chuỗi không được có>
absent() {
  local body
  body=$(curl -s -b "$1" "$APP$2")
  if [[ "$body" == *"$4"* ]]; then
    echo "FAIL       app $3 (không được có: $4)"
    failed=$((failed + 1))
  else
    echo "OK         app $3"
  fi
}

gw() {
  local jar="$1" method="$2" path="$3" body="${4:-}"
  [ -n "$body" ] || body='{}'
  curl -s -b "$jar" -X "$method" -H 'Content-Type: application/json' --data "$body" "$APP/gw/api/data$path"
}

sv=$(login sinhvien)
tp=$(login truongphong)
kt=$(login kythuatvien)

page "$sv" /tickets "danh sách của sinhvien" "Yêu cầu của tôi" "Báo hỏng thiết bị"
# Form có hai nhánh tuỳ profile integration: danh sách thiết bị từ Snipe-IT, hoặc
# thông báo chưa kết nối và chọn vị trí tay. Kiểm tra đúng nhánh đang chạy.
assets_code=$(curl -s -b "$sv" -o /dev/null -w '%{http_code}' "$APP/gw/api/assets/me")
if [ "$assets_code" = 200 ]; then
  page "$sv" /tickets/new "form báo hỏng hiện thiết bị của sinhvien từ hệ thống tài sản" \
    "HAUI-LT-0001" "CS1 · CS1-C-PM401" "Ảnh lỗi" "Gợi ý phân loại"
else
  page "$sv" /tickets/new "form báo hỏng, dự phòng khi chưa có hệ thống tài sản" \
    "Chưa kết nối được hệ thống tài sản" "CS1 · CS1-C-PM401" "Ảnh lỗi" "Gợi ý phân loại"
fi
page "$tp" /tickets "hàng đợi của truongphong" "Hàng đợi CS1"
# Thống kê (#27): trưởng phòng mở được trang; sinh viên chỉ thấy thông báo không có quyền
page "$tp" /dashboard "thống kê của truongphong" "Thống kê Cơ sở 1"
page "$sv" /dashboard "sinhvien không xem được thống kê" "Chỉ trưởng phòng lab và quản trị hệ thống"

title="App smoke: PC-07 phòng C401 treo màn hình $(date +%s)"
id=$(gw "$sv" POST /tickets "{\"title\":\"$title\",\"description\":\"Treo khi mở IDE\",\"category\":\"HARDWARE\",\"priority\":\"MEDIUM\",\"location_id\":6}" \
  | python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])')
page "$sv" "/tickets/$id" "chi tiết bản nháp với người tạo" "$title" "Gửi yêu cầu" "Xoá bản nháp"
gw "$sv" POST "/tickets/$id/actions/submit" >/dev/null
page "$sv" "/tickets/$id" "sinhvien thấy trạng thái chờ tiếp nhận" "Chờ tiếp nhận" "Gửi yêu cầu"
absent "$sv" "/tickets/$id" "sinhvien không thấy nút tiếp nhận" ">Tiếp nhận</button>"
page "$tp" "/tickets/$id" "truongphong thấy tiếp nhận và từ chối" ">Tiếp nhận</button>" "Lý do từ chối"
gw "$tp" POST "/tickets/$id/actions/accept" >/dev/null
page "$tp" "/tickets/$id" "sau tiếp nhận, truongphong thấy phân công" ">Phân công</button>" "Kỹ thuật viên cùng cơ sở CS1"
tech=$(gw "$tp" GET /technicians | python3 -c 'import json,sys; print([t["sub"] for t in json.load(sys.stdin) if t["username"]=="kythuatvien"][0])')
gw "$tp" POST "/tickets/$id/actions/assign" "{\"technician_sub\":\"$tech\"}" >/dev/null
page "$kt" "/tickets/$id" "kythuatvien được giao thấy nhận việc" ">Nhận việc</button>"
absent "$tp" "/tickets/$id" "truongphong không thấy nút nhận việc" ">Nhận việc</button>"
gw "$kt" POST "/tickets/$id/actions/start" >/dev/null
page "$kt" "/tickets/$id" "kythuatvien thấy ô biên bản" "Biên bản xử lý" ">Đánh dấu hoàn thành</button>"
gw "$kt" POST "/tickets/$id/actions/resolve" '{"resolution_summary":"Thay RAM"}' >/dev/null
page "$tp" "/tickets/$id" "truongphong thấy nghiệm thu và mở lại" ">Nghiệm thu và đóng</button>" "Lý do mở lại"
gw "$tp" POST "/tickets/$id/actions/reopen" '{"reason":"Vẫn treo"}' >/dev/null
gw "$kt" POST "/tickets/$id/actions/resolve" '{"resolution_summary":"Cài lại driver"}' >/dev/null
gw "$tp" POST "/tickets/$id/actions/close" >/dev/null
page "$sv" "/tickets/$id" "lịch sử có mở lại, sinhvien thấy ô đánh giá" \
  "Đã đóng" "Mở lại" "Vẫn treo" "Cài lại driver" "Mức độ hài lòng"

[ "$failed" -eq 0 ] || { echo "$failed kiểm tra trang ticket không đạt"; exit 1; }
