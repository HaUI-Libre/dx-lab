<!--
SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
SPDX-License-Identifier: Apache-2.0
-->

# Hướng dẫn đóng góp

Cảm ơn bạn quan tâm đến DX-Lab! Mọi đóng góp đều đi theo quy trình
**Issue → Nhánh → Pull Request → Review → Merge**.

## 1. Bắt đầu từ một Issue

- Tìm Issue có sẵn, hoặc tạo mới bằng mẫu *Báo lỗi* / *Đề xuất tính năng*.
- Người mới nên chọn Issue có nhãn `good first issue`.
- Gán Issue cho mình trước khi làm để tránh trùng việc.

## 2. Tạo nhánh

```bash
git checkout main
git pull
git checkout -b <loại>/<số-issue>-<mô-tả-ngắn>
```

| Loại | Dùng khi | Ví dụ |
|---|---|---|
| `feat` | Tính năng mới | `feat/12-apisix-route` |
| `fix` | Sửa lỗi | `fix/21-login-redirect` |
| `docs` | Tài liệu | `docs/30-readme-install` |
| `chore` | Cấu hình, công cụ | `chore/1-repo-skeleton` |
| `test` | Kiểm thử | `test/40-data-api` |

## 3. Commit

Theo [Conventional Commits](https://www.conventionalcommits.org/vi/):

```
<loại>(<phạm vi>): <mô tả ngắn, thể mệnh lệnh>
```

Ví dụ:

```
feat(core): thêm route /api/data qua APISIX (#12)
fix(app): sửa lỗi chuyển hướng sau khi đăng nhập (#21)
docs: bổ sung hướng dẫn cài đặt
```

Phạm vi gợi ý: `core`, `data`, `ai`, `app`, `docs`, `ci`.

Commit nhỏ, mỗi commit một ý. Cấu hình `git config user.email` trùng với email
tài khoản GitHub để commit được ghi nhận đúng người.

## 4. Pull Request

- Mỗi PR chỉ giải quyết một Issue, nên dưới ~300 dòng thay đổi.
- Điền đầy đủ mẫu PR, ghi `Closes #<số>` để tự đóng Issue.
- Cập nhật nhánh theo `main` trước khi xin review:
  ```bash
  git fetch origin
  git rebase origin/main
  git push --force-with-lease
  ```
  Chỉ dùng `--force-with-lease` trên **nhánh của mình**, không bao giờ trên `main`.
- Cần **1 approval** và **CI xanh** mới được merge. Kiểu merge: *Squash and merge*.

## 5. Quy tắc bắt buộc

- **SPDX header** ở đầu mọi tệp mã và tài liệu:
  ```
  # SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
  # SPDX-License-Identifier: Apache-2.0
  ```
  (Markdown/HTML dùng `<!-- ... -->`, JS/TS dùng `//`.) Kiểm tra: `make check-spdx`.
- **Không commit secret**: mật khẩu, token, API key, file `.env`. Thêm biến mới
  vào `.env.example` với giá trị giả. CI quét bằng gitleaks.
- **Thêm thư viện mới** phải bổ sung dòng tương ứng trong
  [docs/dependencies.md](docs/dependencies.md) (tên, phiên bản, giấy phép, vai trò).
  Chỉ dùng thành phần có giấy phép được OSI chấp thuận.
- **Không sửa mã nguồn của thư viện bên ngoài** trong repo.
- **Giải thích được thay đổi của mình.** Code viết cùng công cụ AI vẫn được chấp
  nhận, nhưng người mở PR phải hiểu và trình bày được nó trong mô tả PR.

## 6. Review

Người review kiểm tra: đúng phạm vi Issue, chạy được, có test khi phù hợp,
có SPDX header, không lộ secret, tài liệu được cập nhật. Góp ý cụ thể, lịch sự.
