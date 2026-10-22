<!--
SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
SPDX-License-Identifier: Apache-2.0
-->

# Kiểm thử BPMN qua gateway (#19)

Sau `make up`, chạy `./scripts/test-workflow-api.sh` để kiểm tra ba nhánh. Có thể chọn
riêng `success`, `reject`, `reopen`, ví dụ `./scripts/test-workflow-api.sh reopen`.
Job CI `Stack từ volume trống` chạy script này sau `make smoke`.
Script dùng `curl` với tài khoản `quantri` để lấy token Keycloak từ `.env`, gọi
Flowable **qua APISIX**, dùng Python 3 thư viện chuẩn để kiểm tra JSON, lấy động
instance ID/task ID và chỉ truy vấn task theo instance ID vừa tạo. Không in
token, client secret hoặc mật khẩu.

Kết quả mong đợi:

| Kịch bản | Thứ tự task trong history | Kết thúc |
|---|---|---|
| `success` | Intake → Assign → TechnicianAccept → Repair → Review | Đã đóng |
| `reject` | Intake | Đã từ chối với lý do |
| `reopen` | Intake → Assign → TechnicianAccept → Repair → Review → Repair → Review | Đã mở lại đúng kỹ thuật viên rồi đóng |

Script kiểm tra HTTP status, task tiếp theo, assignee của hai lượt sửa chữa,
thứ tự và thời gian kết thúc task trong Flowable history. Các biến `ticket_id`,
`co_so`, nhóm ứng viên, `assigned_technician`, `intake_action`, `review_action`
và lý do dùng đúng hợp đồng trong BPMN. Ticket ID là UUID ngẫu nhiên của mỗi lần
chạy. Các request tạo process trong Flowable để kiểm thử engine; Data API chưa
quản lý ticket và trạng thái nghiệp vụ trong kịch bản này (#20).

Không chạy script trên dữ liệu sản xuất: mỗi lần gọi tạo thêm process instance
và history. Các route ghi workflow chỉ dành cho `ROLE_ADMIN` đến khi Data API
cung cấp API nghiệp vụ có kiểm tra quyền và `co_so`.
