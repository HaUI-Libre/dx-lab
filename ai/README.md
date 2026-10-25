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
Dịch vụ chạy mặc định trong Docker Compose bằng `make up`, chỉ mở cổng nội bộ.
APISIX kiểm tra token Keycloak và proxy `POST /api/ai/classify` tới service.
`make smoke` kiểm tra 401 khi thiếu token và gợi ý khi có token. `make up` chỉ dùng
mô hình đã huấn luyện trong image, không tải mô hình từ Internet lúc khởi động.

`train.py` đọc 160 mẫu có nhãn của đội ở `data/samples/training_data.jsonl`, chia tập
kiểm thử riêng rồi huấn luyện hai mô hình TF-IDF + logistic regression. Dockerfile
huấn luyện khi build; `model.joblib` chỉ nằm trong image, không commit vào Git.
Kết quả, giấy phép dữ liệu và giới hạn nằm ở [EVALUATION.md](EVALUATION.md).
Model trả `keywords` là các từ/cặp từ trong mô tả có trọng số dương cao nhất;
`confidence` là xác suất nhỏ hơn giữa hai dự đoán, chỉ dùng để tham khảo.
