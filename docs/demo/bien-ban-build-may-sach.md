<!--
SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
SPDX-License-Identifier: Apache-2.0
-->

# Biên bản build từ mã nguồn trên máy sạch (R.32)

- **Issue:** [#38](https://github.com/HaUI-Libre/dx-lab/issues/38)
- **Ngày ghi:** 25/10/2026, cập nhật 28/10/2026
- **Nguyên tắc:** chỉ ghi số liệu có nguồn kiểm chứng được (log CI hoặc lệnh đã chạy). Mục nào chưa chạy thì ghi "chưa chạy".

## 1. Linux sạch: runner GitHub Actions

Mỗi lần chạy CI dùng một máy ảo `ubuntu-24.04` mới của GitHub, chưa có image, volume hay
`.env` nào của dự án; mọi image bên thứ ba được tải và image của đội được build từ mã nguồn
trong lần chạy đó. Cấu hình runner chuẩn cho repo public theo
[tài liệu GitHub](https://docs.github.com/en/actions/using-github-hosted-runners/about-github-hosted-runners):
4 vCPU, 16 GB RAM. Docker Engine và Compose là bản có sẵn trên image runner, không phải Docker Desktop.

### Toàn bộ chuỗi demo: workflow "Clean machine demo"

Nguồn: [run 40526464778, job 122267292332](https://github.com/HaUI-Libre/dx-lab/actions/runs/40526464778/job/122267292332)
(PR #177, commit `849b79b` trên nền `main` `9c2e293`). Workflow ở
`.github/workflows/clean-demo.yml`; chạy lại bằng Actions > Clean machine demo > Run workflow.

| Mục | Giá trị |
|---|---|
| Docker | Docker Engine 28.0.4, Docker Compose v2.38.2 |
| Trạng thái trước khi chạy | 6 image có sẵn của image runner, 0 volume, chưa có `.env` |
| Cách gọi | Mọi lệnh chạy từ `$RUNNER_TEMP` bằng `make -C <thư mục repo> <đích>`, tức ngoài thư mục repo |
| Tổng thời gian job | 3 phút 54 giây (14:59:17 tới 15:03:11 UTC) |

| Lệnh (đo bằng `time`) | Thời gian | Kết quả |
|---|---|---|
| `make env` | 0,03 giây | đạt |
| `make demo` (build `app`, `ai`, `asset-sync`, `data-api`; tải image bên thứ ba; chờ healthy mọi profile; deploy BPMN) | 2 phút 46 giây | đạt |
| `make seed` | 1,6 giây | đạt |
| `make smoke` | 16,9 giây | 137 kiểm tra đạt, 0 lỗi |
| `make smoke-assets` | 30,1 giây | 9 kiểm tra đạt, 0 lỗi |
| `make smoke-monitoring` | 0,16 giây | 11 kiểm tra đạt, 0 lỗi (2 dòng thông tin: target `asset-sync`, `nats` lên) |
| `make test-e2e` | 8,4 giây | 31 đạt, 1 bỏ qua, 0 lỗi |

Bước bỏ qua của `make test-e2e` là 2.3 "AI không phản hồi": dịch vụ phân loại đang chạy nên
không thử được nhánh lỗi; script ghi rõ không tính là đạt. Nhánh này có test tự động riêng ở
`tests/test_ai_http.py`.

Dung lượng Docker sau khi chạy (`docker system df`): image 7,909 GB (23 image), volume
692,7 MB (9 volume), build cache 244,9 MB, 16 container.

### Các job CI khác trên máy sạch

Hai job dưới đây chạy trên mọi PR chạm hạ tầng, cũng trên runner mới.

Profile mặc định, job "Stack từ volume trống". Nguồn:
[lần chạy của PR #130, job 121090874733](https://github.com/HaUI-Libre/dx-lab/actions/runs/40167303524/job/121090874733).

| Bước (lệnh trong `.github/workflows/stack.yml`) | Thời gian | Kết quả |
|---|---|---|
| `make env` | dưới 1 giây | đạt |
| `docker compose build` (image `data-api`, `app`, `workflow-deploy`) | 23 giây | đạt |
| `make up` (tải image bên thứ ba, chờ healthcheck, deploy BPMN) | 77 giây | đạt |
| `make seed` | 1 giây | đạt |
| `make smoke` | 11 giây | 111 kiểm tra đạt, 0 lỗi |
| `scripts/test-workflow-api.sh` (ba nhánh BPMN) | 1 giây | đạt |

Profile integration, job "asset-flow". Nguồn:
[lần chạy của PR #128, job 121084112069](https://github.com/HaUI-Libre/dx-lab/actions/runs/40164993051/job/121084112069).

| Bước (`.github/workflows/asset-integration.yml`) | Thời gian | Kết quả |
|---|---|---|
| Build `data-api`, `app`, `asset-sync` | 52 giây | đạt |
| `make up` (lõi, deploy BPMN) | 111 giây | đạt |
| Khởi động MariaDB, Snipe-IT, `asset-sync` | 71 giây | đạt |
| `make smoke-assets` | 24 giây | đạt |

## 2. Windows 11 qua WSL2

### Máy sạch: kết quả

Nguồn: log `bien-ban-38.log` do thaolinh657 chạy theo các bước dưới đây, gửi ngày 28/10/2026.
Log ghi output của `wsl --version`, `uname -r`, `docker version`, `docker compose version`, từng
lệnh `time make ...` và `docker system df`. Mọi lệnh gọi bằng `make -C`, thư mục repo là
`/home/linh/dx-lab` (dòng `make: Entering directory`). Trước `make env` chưa có `.env`: lệnh
báo "Đã tạo .env với khoá ngẫu nhiên". Log không ghi tên bản WSL, bản Linux, CPU, bộ nhớ hay
commit đã clone, nên các mục này để trống.

| Mục | Giá trị |
|---|---|
| Máy | Windows build 10.0.26200.9711; WSL 3.0.3.0, WSLg 1.0.79 |
| Bản Linux, kernel | không có trong log; kernel 6.18.54.1-microsoft-standard-WSL2 |
| Docker | Docker Engine 29.9.2, Docker Compose v5.6.1; không dùng Docker Desktop |
| Tổng thời gian các lệnh | khoảng 44 phút 36 giây, gần hết là `make demo` |

| Lệnh (đo bằng `time`) | Thời gian | Kết quả |
|---|---|---|
| `make env` | 0,12 giây | đạt, sinh `.env` mới |
| `make demo` (tải image bên thứ ba, build `app`, `ai`, `asset-sync`, `data-api`, `workflow-deploy`; chờ healthy mọi profile; deploy BPMN) | 43 phút 26 giây | đạt, 16 container healthy, deploy `dxlabHelpdeskRepair` v1 |
| `make seed` | 3,6 giây | đạt |
| `make smoke` | 25,0 giây | 137 kiểm tra đạt, 0 lỗi |
| `make smoke-assets` | 31,1 giây | 9 kiểm tra đạt, 0 lỗi |
| `make smoke-monitoring` | 0,26 giây | 11 kiểm tra đạt, 0 lỗi (2 dòng thông tin: target `asset-sync` xuống, `nats` lên) |
| `make test-e2e` | 10,1 giây | 31 đạt, 1 bỏ qua, 0 lỗi |

`make demo` chậm hơn runner CI (2 phút 46 giây) chủ yếu vì tải khoảng 8,7 GB image qua mạng của
máy; thời gian CPU của lệnh chỉ khoảng 24 giây. Bước bỏ qua của `make test-e2e` vẫn là 2.3 "AI
không phản hồi", giống mục 1. Dòng `target asset-sync xuống` của `make smoke-monitoring` giống
lần chạy CI: không làm lệnh thất bại, `make smoke-assets` ngay trước đó đã đạt.

Không gặp lỗi nào trong log; chỉ có cảnh báo khi build image (`pip` chạy bằng root, `npm`
báo `glob@10.5.0` đã cũ), không ảnh hưởng kết quả.

Dung lượng Docker sau khi chạy (`docker system df`): image 8,693 GB (18 image), volume
637,4 MB (9 volume), build cache 1,346 GB, 16 container.

### Cách chạy trên máy sạch

Đội không có máy Windows mới, nên cách làm dưới đây tạo **một bản WSL mới tinh** trên máy
Windows đang có: bản này chưa
có Docker, image, volume, `.env` hay repo nào, tức là sạch với mọi thứ dự án dùng. Windows host
thì không mới; biên bản phải ghi rõ điều này.

Theo #38, người chạy là một thành viên không viết phần hạ tầng (thaolinh657), chỉ dùng các
bước trong README. Thời gian dự kiến 1 đến 2 giờ, chủ yếu là tải image (khoảng 8 GB, xem mục 1).

**Bước 1. Chuẩn bị (PowerShell trên Windows).**

```powershell
wsl --version            # ghi lại số phiên bản WSL
wsl --list --verbose     # các bản WSL đang có
```

Các bản WSL2 chạy chung một máy ảo và một mạng: cổng `127.0.0.1:3000`, `8080`, `9080` và mạng
`docker0` bị trùng nếu một bản WSL khác đang chạy Docker. Nếu có, dừng Docker trong bản đó
trước (ví dụ `wsl -d <tên bản cũ> -u root systemctl stop docker docker.socket`) và bật lại sau
khi xong (`systemctl start docker`).

**Bước 2. Tạo bản WSL mới (PowerShell).** README dùng bản `Ubuntu`:

```powershell
wsl --install Ubuntu --name dxlab-clean
```

Máy không nhận tuỳ chọn `--name` (WSL cũ) thì tải tệp rootfs Ubuntu chính thức (trang
cloud-images.ubuntu.com, bản `wsl` của Ubuntu LTS) rồi:

```powershell
wsl --import dxlab-clean C:\wsl\dxlab-clean <đường-dẫn-tệp-rootfs>
```

Mở bản mới bằng `wsl -d dxlab-clean`, tạo tài khoản Linux khi được hỏi.

**Bước 3. Cài đặt theo README (trong `dxlab-clean`).**

- Cài Docker Engine và Compose plugin theo
  [hướng dẫn cho Ubuntu](https://docs.docker.com/engine/install/ubuntu/), rồi
  `sudo apt install make curl git`. Không dùng Docker Desktop.
- Ghi lại `docker version` và `docker compose version`.
- Clone trong hệ thống tệp của WSL: `git clone https://github.com/HaUI-Libre/dx-lab.git ~/dx-lab`.

**Bước 4. Chạy và đo (trong `dxlab-clean`, từ thư mục ngoài repo).**

```bash
cd ~
time make -C ~/dx-lab env
time make -C ~/dx-lab demo
time make -C ~/dx-lab seed
time make -C ~/dx-lab smoke
time make -C ~/dx-lab smoke-assets
time make -C ~/dx-lab smoke-monitoring
time make -C ~/dx-lab test-e2e
docker system df
```

Lưu toàn bộ output (ví dụ thêm `2>&1 | tee -a ~/bien-ban.log` sau mỗi lệnh), đính kèm vào
Issue #38 và ghi kết quả vào mục "Máy sạch: kết quả" ở trên.

**Bước 5. Gỡ bản WSL sau khi xong (PowerShell).** Xoá hẳn bản `dxlab-clean` cùng mọi dữ liệu
trong đó, giải phóng khoảng 10 GB:

```powershell
wsl --unregister dxlab-clean
```

Nhớ bật lại Docker trong bản WSL cũ nếu đã dừng ở bước 1.

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
| Gateway trả 502 sau khi build lại một container | APISIX còn giữ IP cũ của container trong bộ nhớ đệm DNS | `make up` và `make demo` tự khởi động lại APISIX (#176); dựng tay thì `docker compose restart apisix` |
| `eth0` của WSL xuống sau khi WSL khởi động lại, mất mạng khi kéo image | Cấu hình mạng của bản phân phối | `sudo ip link set eth0 up` rồi thêm lại default route |

## 4. Kết luận

- Linux sạch: toàn bộ chuỗi trong README (`make env`, `demo`, `seed`, `smoke`, `smoke-assets`,
  `smoke-monitoring`, `test-e2e`) đạt trên một runner mới, gọi bằng `make -C` từ ngoài thư mục
  repo, tổng 3 phút 54 giây; số liệu ở mục 1.
- Windows qua WSL2, không dùng Docker Desktop: cùng chuỗi lệnh đạt trên một môi trường chưa
  có `.env`, gọi bằng `make -C`, tổng khoảng 44 phút 36 giây (gần hết là tải image); số liệu ở
  mục 2. Log không ghi tên bản WSL nên chưa đối chiếu được đó là bản `dxlab-clean` mới tạo.
