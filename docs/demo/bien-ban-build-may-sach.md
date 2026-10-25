<!--
SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
SPDX-License-Identifier: Apache-2.0
-->

# Biên bản build từ mã nguồn trên máy sạch (R.32)

- **Issue:** [#38](https://github.com/HaUI-Libre/dx-lab/issues/38)
- **Ngày ghi:** 25/10/2026
- **Nguyên tắc:** chỉ ghi số liệu có nguồn kiểm chứng được (log CI hoặc lệnh đã chạy). Mục nào chưa chạy thì ghi "chưa chạy".

## 1. Linux sạch: runner GitHub Actions

Mỗi lần chạy CI dùng một máy ảo `ubuntu-24.04` mới của GitHub, chưa có image, volume hay
`.env` nào; mọi image bên thứ ba được tải và image của đội được build từ mã nguồn trong
lần chạy đó. Cấu hình runner chuẩn cho repo public theo
[tài liệu GitHub](https://docs.github.com/en/actions/using-github-hosted-runners/about-github-hosted-runners):
4 vCPU, 16 GB RAM. Docker Engine và Compose là bản có sẵn trên image runner, không phải Docker Desktop.

### Profile mặc định: job "Stack từ volume trống"

Nguồn: [lần chạy của PR #130, job 121090874733](https://github.com/HaUI-Libre/dx-lab/actions/runs/40167303524/job/121090874733) (commit trên nền `main`).

| Bước (lệnh trong `.github/workflows/stack.yml`) | Thời gian | Kết quả |
|---|---|---|
| `make env` | dưới 1 giây | đạt |
| `docker compose build` (image `data-api`, `app`, `workflow-deploy`) | 23 giây | đạt |
| `make up` (tải image bên thứ ba, chờ healthcheck, deploy BPMN) | 77 giây | đạt |
| `make seed` | 1 giây | đạt |
| `make smoke` | 11 giây | 111 kiểm tra đạt, 0 lỗi |
| `scripts/test-workflow-api.sh` (ba nhánh BPMN) | 1 giây | đạt |

### Profile integration: job "asset-flow"

Nguồn: [lần chạy của PR #128, job 121084112069](https://github.com/HaUI-Libre/dx-lab/actions/runs/40164993051/job/121084112069).

| Bước (`.github/workflows/asset-integration.yml`) | Thời gian | Kết quả |
|---|---|---|
| Build `data-api`, `app`, `asset-sync` | 52 giây | đạt |
| `make up` (lõi, deploy BPMN) | 111 giây | đạt |
| Khởi động MariaDB, Snipe-IT, `asset-sync` | 71 giây | đạt |
| `make smoke-assets` | 24 giây | đạt |

### Chưa chạy trên Linux sạch

- `make smoke-monitoring` và `make test-e2e`: CI chưa có job cho profile `monitoring` và chuỗi e2e. Đã chạy trên máy Windows ở mục 2 (không phải máy sạch).

## 2. Windows 11 qua WSL2

### Máy sạch: chưa chạy

Chưa có lần cài trên một máy Windows chưa từng chạy dự án. Cần làm để đóng #38:
clone vào máy mới, cài Docker Engine trong bản Linux của WSL2 theo README, chạy `make env`,
`make up`, `make smoke`, `make demo`, `make smoke-assets`, `make smoke-monitoring`,
`make test-e2e`; ghi lại bằng `time make ...` và đính kèm output vào Issue #38.

### Máy phát triển (không sạch): số liệu tham khảo

Đã có sẵn image và một stack đang chạy, nên không đo được thời gian build và tải image.

| Mục | Giá trị |
|---|---|
| Máy | Windows 11 Pro build 26200, WSL 3.0.3.0, Kali GNU/Linux Rolling, kernel 6.18.54.1-microsoft-standard-WSL2 |
| CPU, bộ nhớ cho WSL | Intel Core i7-9750H, 12 luồng; 15 GB |
| Docker | Docker Engine 28.5.2, Compose 2.40.3; không dùng Docker Desktop |

| Lệnh | Thời gian | Kết quả |
|---|---|---|
| `make -C <đường-dẫn-repo> ps` gọi từ `/tmp` | dưới 1 giây | đạt, liệt kê 15 service đang chạy |
| `make -C <đường-dẫn-repo> smoke` gọi từ `/tmp` | 17 giây | 111 đạt, 0 lỗi |
| `make test-e2e` (2 lần liên tiếp) | 12,3 và 10,3 giây | 31 đạt, 2 bỏ qua, 0 lỗi; xem `docs/demo/bien-ban-test-e2e.md` |

## 3. Lỗi đã gặp khi chạy trên WSL2 và cách xử lý

| Hiện tượng | Nguyên nhân | Cách xử lý |
|---|---|---|
| Script `.sh` báo `bad interpreter` | Git trên Windows đổi xuống dòng sang CRLF | Repo có `.gitattributes` giữ LF cho `*.sh`, `Makefile`, `*.yml`; clone lại nếu tệp đã bị đổi trước đó |
| `make up` dừng ở `env-check` | `DATA_WORKFLOW_KEY` trong `.env` vẫn là `changeme` | Dùng `make env` để sinh khoá, hoặc đặt một chuỗi ngẫu nhiên dài |
| Gateway trả 502 sau khi build lại một container | APISIX còn giữ IP cũ của container trong bộ nhớ đệm DNS | `docker compose restart apisix` |
| `eth0` của WSL xuống sau khi WSL khởi động lại, mất mạng khi kéo image | Cấu hình mạng của bản phân phối | `sudo ip link set eth0 up` rồi thêm lại default route |

## 4. Kết luận

- Linux sạch: build từ mã nguồn, `make up`, `make seed`, `make smoke` và `make smoke-assets` đạt trên runner mới, số liệu ở mục 1.
- Windows sạch: chưa chạy. #38 còn mở cho tới khi có biên bản ở mục 2.
