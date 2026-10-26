<!--
SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
SPDX-License-Identifier: Apache-2.0
-->

# ai/

Dịch vụ Intelligence gợi ý loại sự cố và mức ưu tiên; người dùng xác nhận hoặc sửa
trước khi gửi ticket. `POST /classify` nhận `title`, `description`, trả `category`,
`priority`, `keywords` và `source` (`model` hoặc `rules`).

`rules.py` dùng từ khóa tiếng Việt để dự phòng khi mô hình chưa có, lỗi hoặc chạy quá
`AI_MODEL_TIMEOUT_SECONDS` (mặc định 1 giây). Từ khóa khớp được trả để giải thích.
Nếu không khớp loại nào, API trả 422 để người dùng chọn thủ công, không tự bịa loại.
Mức ưu tiên chỉ là gợi ý; luật không đổi trạng thái ticket hoặc quyền người dùng.

Chạy riêng trong môi trường phát triển: `uvicorn app:app --app-dir ai --port 8000`.
Dịch vụ đi qua APISIX và Docker Compose ở issue #31.

## Cài bằng pip, chạy ngoài Docker

`pip install .` trong venv cài dịch vụ cùng hai lệnh `dxlab-ai-train` (huấn luyện) và
`dxlab-ai-classifier` (chạy server), chạy được từ thư mục bất kỳ. Đặt `AI_MODEL_PATH`
trỏ tới model đã huấn luyện trước khi chạy server; không đặt thì dịch vụ chỉ trả lời
bằng luật từ khóa (`source: "rules"`). Chi tiết:
[docs/build-from-source.md](../docs/build-from-source.md) mục 3.
