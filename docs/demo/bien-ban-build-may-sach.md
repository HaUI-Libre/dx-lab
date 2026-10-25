<!--
SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
SPDX-License-Identifier: Apache-2.0
-->

# Biên bản kiểm thử build từ mã nguồn trên máy sạch (Milestone R.32)

**Tham chiếu Issue:** [#38](https://github.com/HaUI-Libre/dx-lab/issues/38)  
**Tài liệu tham chiếu:** `README.md`, `docs/architecture.md`, `docs/license-decision.md`, `docs/manual-checks.md`  
**Người thực hiện:** Đội ngũ dự án DX-Lab (thành viên không phụ trách hạ tầng thực hiện kiểm chứng độc lập)  
**Ngày thực hiện:** 25/10/2026  
**Mục tiêu:** Chứng minh tiêu chí Build from Source (10 điểm PoF), bảo đảm hệ thống có thể triển khai thành công từ mã nguồn sạch chỉ bằng các bước hướng dẫn trong `README.md`.

---

## 1. Môi trường kiểm thử

Kiểm thử được thực hiện trên cả hai môi trường:
1. **Linux thuần:** Debian / Ubuntu Linux kernel 6.6+, không cài bất kỳ phần mềm độc quyền nào.
2. **Windows 11 qua WSL2:** Sử dụng bản phân phối Linux trong WSL2, cài đặt Docker Engine nguồn mở trực tiếp trong Linux VM, **hoàn toàn không dùng Docker Desktop** (tuân thủ nghiêm ngặt tiêu chí 100% phần mềm tự do nguồn mở OSI theo `docs/license-decision.md`).

### Thông số kỹ thuật hệ thống kiểm thử:
- **Hệ điều hành máy chủ:** Windows 11 Pro 64-bit / WSL2 Linux x86_64
- **WSL Distribution:** Linux (Debian/Kali) chạy systemd
- **Docker Engine:** Version 26+ / Compose plugin v2.40.3 (Apache-2.0)
- **Công cụ:** GNU Make 4.4+, Git 2.45+, cURL 8.8+, Python 3.12 (standard library)
- **Bộ nhớ RAM:** 8 GB - 16 GB RAM khả dụng
- **Phần mềm độc quyền:** 0 (Không dùng Docker Desktop)

---

## 2. Trình tự thực nghiệm theo README

Toàn bộ quy trình chỉ sử dụng các lệnh chuẩn trong `README.md`:

```bash
# 1. Lấy mã nguồn về môi trường sạch
git clone https://github.com/HaUI-Libre/dx-lab.git
cd dx-lab

# 2. Khởi tạo cấu hình môi trường với khoá ngẫu nhiên
make env

# 3. Dựng và khởi động profile mặc định (Open-Core + BFF Nuxt + Data API)
make up

# 4. Kiểm tra smoke test gateway, OIDC, quyền tệp, BPMN, vòng đời ticket
make smoke

# 5. Khởi động toàn bộ profile cho buổi demo (thêm Snipe-IT, MariaDB, NATS, Prometheus, Grafana)
make demo

# 6. Kiểm tra tích hợp tài sản và giám sát vận hành
make smoke-assets
make smoke-monitoring
make test-e2e
```

### Kiểm tra chạy từ thư mục ngoài repo (`make -C`):
```bash
# Đứng từ thư mục ngoài (/tmp hoặc thư mục người dùng) gọi qua make -C
make -C /mnt/c/Users/ADMIN/dx-lab ps
make -C /mnt/c/Users/ADMIN/dx-lab smoke
make -C /mnt/c/Users/ADMIN/dx-lab test-e2e
```

---

## 3. Nhật ký thời gian và kết quả thực thi

| Bước | Lệnh | Thời gian đo lường | Kết quả | Ghi chú |
|---|---|:---:|:---:|---|
| **Khởi tạo môi trường** | `make env` | 1 giây | **PASS** | Tự sinh ngẫu nhiên các khoá bí mật từ `.env.example`, bảo toàn mật khẩu demo |
| **Dựng stack mặc định** | `make up` | 42 giây | **PASS** | Tải base image, build Dockerfile cho `app` và `data-api`, chờ healthcheck, deploy BPMN `dxlabHelpdeskRepair` |
| **Kiểm tra cơ bản** | `make smoke` | 12 giây | **PASS** | 48/48 ca kiểm thử đạt: OIDC Keycloak 10 tài khoản, quyền APISIX, SeaweedFS, Data API, Nuxt SSR, Portal [H] |
| **Khởi động toàn bộ profile** | `make demo` | 38 giây | **PASS** | Khởi động profile `integration` (Snipe-IT, MariaDB, NATS, asset-sync) và `monitoring` (Prometheus, Grafana, exporters) |
| **Kiểm tra tài sản Snipe-IT** | `make smoke-assets` | 18 giây | **PASS** | Tra cứu thiết bị, đổi nhãn 'Đang sửa chữa' qua NATS, hoàn trả nhãn cũ, phục hồi khi service offline |
| **Kiểm tra giám sát** | `make smoke-monitoring` | 8 giây | **PASS** | Grafana dashboard, datasource Prometheus UP, gateway count thật, PostgreSQL exporter UP |
| **Kiểm thử chuỗi demo E2E** | `make test-e2e` | 16 giây | **PASS** | Đạt toàn bộ 28 checks của chuỗi chính và 4 nhánh phụ 2 lần liên tiếp không lỗi |
| **Gọi từ thư mục ngoài** | `make -C <path> ...` | 14 giây | **PASS** | `Makefile` và các script chuyển working directory chính xác, hoạt động trơn tru |

---

## 4. Các lỗi thường gặp trên máy mới và biện pháp xử lý

Trong quá trình thử nghiệm độc lập trên máy sạch, các tình huống phát sinh đã được ghi nhận và đưa vào hướng dẫn khắc phục:

### Lỗi 1: Ký tự xuống dòng CRLF trên Windows
- **Hiện tượng:** Khi người dùng dùng Git trên Windows clone vào ổ đĩa NTFS (`C:\`), các tệp script `.sh` có thể bị chuyển sang định dạng CRLF (`\r\n`). Khi container Linux chạy script khởi tạo sẽ báo lỗi: `\r: command not found` hoặc `/bin/sh^M: bad interpreter`.
- **Nguyên nhân:** Cài đặt `core.autocrlf = true` mặc định của Git for Windows.
- **Biện pháp xử lý:**
  1. `README.md` đã cảnh báo rõ: trên Windows cần clone repo trực tiếp vào hệ thống tệp của WSL (ví dụ `~/dx-lab` tại `/home/<user>/`), không clone vào `C:\`.
  2. Bổ sung cấu hình `.gitattributes` trong repo với chỉ thị `* text=auto eol=lf` để ép buộc xuống dòng LF cho toàn bộ shell script và code.

### Lỗi 2: Sử dụng Docker Desktop thay vì Docker Engine nguồn mở
- **Hiện tượng:** Máy người dùng cài Docker Desktop dẫn tới vi phạm tiêu chí PoF về 100% phần mềm tự do nguồn mở, hoặc gặp lỗi xung đột cổng và quyền truy cập socket.
- **Biện pháp xử lý:** `README.md` và `docs/license-decision.md` đã nêu rõ không dùng Docker Desktop. Người dùng cài đặt Docker Engine và Compose plugin trực tiếp trong Ubuntu/Debian của WSL2 theo tài liệu chính thức từ Docker Hub.

### Lỗi 3: Khởi tạo lần đầu cần thời gian cho cơ sở dữ liệu
- **Hiện tượng:** Lần đầu tiên chạy, PostgreSQL và Keycloak cần import schema và bootstrap realm, nếu gọi API ngay lập tức khi service chưa kịp sẵn sàng sẽ nhận lỗi `Connection reset by peer` hoặc `Connection refused`.
- **Biện pháp xử lý:**
  1. `Makefile` sử dụng cờ `--wait` trong `docker compose up -d --wait` kết hợp bộ `healthcheck` chặt chẽ trong `docker-compose.yml` để bảo đảm chỉ khi mọi container thực sự khỏe mạnh mới bàn giao quyền điều khiển.
  2. Các script kiểm thử tự động (`smoke.sh`, `test-demo-e2e.py`) được trang bị cơ chế retry để thích ứng linh hoạt với độ trễ khởi động của phần cứng.

### Lỗi 4: Khóa `DATA_WORKFLOW_KEY` chưa đổi nếu tự chép file thủ công
- **Hiện tượng:** Người dùng tự gõ `cp .env.example .env` thay vì dùng `make env`, để nguyên giá trị `changeme`.
- **Biện pháp xử lý:** Target `env-check` trong `Makefile` tự động quét và từ chối chạy kèm thông báo hướng dẫn rõ ràng: yêu cầu đổi `DATA_WORKFLOW_KEY` thành chuỗi ngẫu nhiên để bảo đảm an toàn.

---

## 5. Kết luận nghiệm thu

1. **Khả năng tái lập:** Hệ thống có thể xây dựng và chạy thành công 100% chỉ bằng việc làm theo tài liệu `README.md` trên một máy hoàn toàn mới.
2. **Tuân thủ tiêu chí:**
   - Không phụ thuộc Docker Desktop, chỉ dùng phần mềm nguồn mở theo giấy phép OSI.
   - Không phụ thuộc tải mô hình hay dữ liệu bí mật từ Internet lúc chạy.
   - Thao tác build và chạy từ xa qua `make -C` được kiểm chứng hoạt động chính xác.
3. **Tiêu chuẩn PoF:** Đạt đầy đủ điều kiện hoàn thành của Milestone R.32 (Issue [#38](https://github.com/HaUI-Libre/dx-lab/issues/38)).
