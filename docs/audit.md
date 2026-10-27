<!--
SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
SPDX-License-Identifier: Apache-2.0
-->

# Rà soát giấy phép và secret (#37)

Chạy lại các bước dưới đây trên đúng tag `v1.0.0` khi phát hành (#39) và cập nhật kết quả.

## Kết quả tại `main` 9c2e293 (27/10/2026)

Commit sau #174, #175, #176; 89 commit trên `main`. Lần rà trước ở `98368b3` (23/10/2026)
có 121 tệp và 45 commit.

**Giấy phép từng tệp.** CI job `REUSE lint` (reuse 6.2.0, REUSE Specification 3.3),
run [40519408616](https://github.com/HaUI-Libre/dx-lab/actions/runs/40519408616); chạy
lại `reuse lint` trên máy cho cùng kết quả:

```
* Bad licenses: 0
* Deprecated licenses: 0
* Licenses without file extension: 0
* Missing licenses: 0
* Unused licenses: 0
* Used licenses: Apache-2.0, CC-BY-4.0
* Read errors: 0
* Invalid SPDX License Expressions: 0
* Files with copyright information: 182 / 182
* Files with license information: 182 / 182
Congratulations! Your project is compliant with version 3.3 of the REUSE Specification :-)
```

CC-BY-4.0 chỉ dùng cho `CODE_OF_CONDUCT.md` (bản dịch Contributor Covenant 2.1).

**Secret trong lịch sử.** CI job `Secret scan (gitleaks)` (gitleaks 8.24.2,
`gitleaks git . --redact` trên toàn bộ lịch sử, `fetch-depth: 0`, gồm mọi nhánh và tag
trên remote), cùng run:

```
87 commits scanned.
no leaks found
```

`.env` không có trong repo (`.gitignore`); `.env.example` chỉ có giá trị giả
`changeme`, `make env` sinh giá trị thật trên từng máy.

**Dữ liệu cá nhân.** Quét email, số điện thoại Việt Nam và số CCCD trên cây hiện tại và mọi
dòng thêm vào trong lịch sử, mọi nhánh; chỉ in vị trí, không in giá trị:

- Email thật duy nhất: `CODE_OF_CONDUCT.md:44`, kênh báo vi phạm do đội công bố có chủ đích.
- Email trong dữ liệu mẫu và test đều thuộc miền `dxlab.local`.
- Các vị trí khác mà bộ quét báo trong `data/app.py`, `ai/app.py`,
  `integration/assets/app.py` và `tests/` là báo nhầm: dòng diff `+@app.get(...)`,
  `+@pytest.fixture` khớp mẫu email, không phải địa chỉ thật.
- Không có số điện thoại hay số CCCD.

**Tệp không chứa được comment.** Cả 14 tệp JSON, JSONL và ảnh trong repo đều có tệp
`<tên-tệp>.license` nằm cạnh:

| Nhóm | Tệp |
|---|---|
| Ứng dụng | `app/package.json`, `app/package-lock.json`, `app/tsconfig.json` |
| Cấu hình | `core/identity/realm-dxlab.json`, `core/monitoring/grafana/dashboards/dxlab-overview.json` |
| Dữ liệu mẫu | `data/samples/campuses.json`, `guides.json`, `snipeit_seed.json`, `tickets.json`, `training_data.jsonl` |
| Sơ đồ | `docs/images/architecture-3-tier.svg`, `helpdesk-workflow.svg`, `integration-architecture.svg`, `service-flow.svg` |

Lệnh kiểm tra:

```bash
git ls-files | grep -Ei '\.(json|jsonl|png|jpe?g|svg|webp|gif|ico)$' \
  | while read f; do [ -f "$f.license" ] || echo "THIẾU: $f"; done
```

## Thành phần bên ngoài

Phiên bản và giấy phép của mọi image, thư viện đang dùng đã đọc tại đúng tag, ghi
trong `docs/license-decision.md` mục 6 và `docs/dependencies.md`; NOTICE liệt kê đủ
thành phần chạy trong `docker-compose.yml`, kể cả profile `integration` và
`monitoring`. Phần lõi chỉ dùng giấy phép OSI; copyleft mạnh (Snipe-IT, Grafana AGPL;
MariaDB, PostGIS GPL) chỉ ở dịch vụ chạy riêng, không liên kết với mã của đội.
