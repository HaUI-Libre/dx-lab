<!--
SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
SPDX-License-Identifier: Apache-2.0
-->

# Đánh giá mô hình gợi ý

Chạy `python ai/train.py --data data/samples/training_data.jsonl --output /tmp/dxlab-ai-model.joblib`
với scikit-learn 1.7.2. Tập 160 mẫu tiếng Việt do đội viết, giấy phép Apache-2.0;
SHA-256 `24b60b906ec110363a1868e659c55c1771578d15f0713a1682b5b4f37a416c31`.
Chia 120 mẫu huấn luyện, 40 mẫu kiểm thử độc lập bằng `random_state=42`, phân tầng
theo cặp loại và ưu tiên. TF-IDF từ và cặp từ + logistic regression cân bằng lớp
được huấn luyện riêng cho hai nhãn. Tập kiểm thử không tham gia `fit`.

| Nhãn | Accuracy | Macro F1 |
|---|---:|---:|
| Loại sự cố | 0,9000 | 0,8981 |
| Mức ưu tiên | 0,5750 | 0,5995 |

Ma trận nhầm lẫn: hàng là nhãn thật, cột là nhãn dự đoán.

**Loại:** thứ tự `HARDWARE`, `LAB_ASSET`, `NETWORK_ACCOUNT`, `SOFTWARE_ENVIRONMENT`.

```text
10  0  0  0
 1  8  1  0
 0  0  8  2
 0  0  0 10
```

**Ưu tiên:** thứ tự `HIGH`, `LOW`, `MEDIUM`, `URGENT`.

```text
8  1  2  1
1  8  3  0
1  7  4  0
1  0  0  3
```

Giới hạn: tập mẫu nhỏ và do đội tự viết, chưa đại diện cho lời báo hỏng thực tế.
Đặc biệt mức ưu tiên `MEDIUM` dễ bị nhầm thành `LOW`; không dùng gợi ý để tự động
chốt ưu tiên hoặc chuyển trạng thái. API trả các từ/cặp từ có trọng số dương lớn
nhất cho nhãn được dự đoán để giải thích, nhưng đây không phải bằng chứng nhân quả.
Khi không tải được mô hình hoặc quá thời gian, dịch vụ dùng luật từ khóa (#30).
