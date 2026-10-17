<!--
SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
SPDX-License-Identifier: Apache-2.0
-->

# Hướng dẫn đóng góp

Mọi đóng góp đi theo quy trình: Issue, nhánh, Pull Request, review rồi merge. Quy ước
dưới đây lấy từ các dự án lớn cùng giấy phép Apache-2.0 (Kubernetes, Keycloak,
Apache APISIX, Apache Airflow), nguồn ghi ở mục 8.

Khi tham gia, bạn đồng ý tuân theo [Quy tắc ứng xử](CODE_OF_CONDUCT.md).

## 1. Bắt đầu từ một Issue

- Tìm Issue có sẵn, hoặc tạo mới bằng mẫu *Báo lỗi* / *Đề xuất tính năng*.
- Người mới nên chọn Issue có nhãn `good first issue`.
- Gán Issue cho mình trước khi làm để tránh trùng việc.

## 2. Tạo nhánh

Tạo nhánh từ `main` mới nhất, tên theo dạng `<loại>/<số-issue>-<mô-tả-ngắn>`:

```bash
git switch main
git pull --ff-only
git switch -c <loại>/<số-issue>-<mô-tả-ngắn>
```

| Loại | Dùng khi | Ví dụ |
|---|---|---|
| `feat` | Tính năng mới | `feat/12-apisix-route` |
| `fix` | Sửa lỗi | `fix/21-login-redirect` |
| `docs` | Tài liệu | `docs/30-readme-install` |
| `chore` | Cấu hình, công cụ, phát hành | `chore/1-repo-skeleton` |
| `test` | Kiểm thử | `test/40-data-api` |
| `ci` | Workflow GitHub Actions | `ci/45-reuse-lint` |
| `refactor` | Sửa cấu trúc mã, không đổi hành vi | `refactor/50-data-repo` |

Mô tả ngắn viết thường, không dấu, nối bằng `-`. Không tạo nhánh tên người
(`hoang/feature`) hay tên chung chung (`develop`, `fix`).

## 3. Commit

### Định dạng

```
<loại>(<phạm vi>): <tiêu đề>

<thân: thay đổi gì và vì sao>

Closes #<số>
Signed-off-by: Họ Tên <email>
```

Loại giống bảng ở mục 2. Phạm vi không bắt buộc, chọn trong `core`, `data`, `ai`,
`app`, `docs`, `ci`, `deps`, `release`.

### Quy tắc

- **Tiêu đề thể mệnh lệnh**, như đang ra lệnh cho repo: "thêm route /api/data",
  không viết "đã thêm" hay "thêm route mới cho API data nhé".
- **Tiêu đề không quá 72 ký tự**, tính cả `<loại>(<phạm vi>): `; nên giữ khoảng 50.
- **Không dấu chấm cuối tiêu đề.**
- **Một dòng trống** giữa tiêu đề và thân.
- **Thân giải thích vì sao.** Diff đã cho thấy sửa gì; thân trả lời vì sao cần sửa,
  vì sao chọn cách này. Ngắt dòng ở 72 ký tự. Commit rất nhỏ (sửa chính tả) có thể
  bỏ thân.
- **Dòng cuối `Closes #<số>`** để liên kết Issue (theo Keycloak). Dùng `Refs #<số>`
  nếu commit chỉ là một phần của Issue.
- **Mỗi commit một ý.** Không gộp sửa định dạng với thay đổi logic.

Ví dụ:

```
feat(core): thêm route /api/data qua APISIX

Data API cần đi qua gateway để dùng chung xác thực Keycloak. Route
kiểm tra vai trò bằng plugin dxlab-roles thay vì để Data API tự kiểm
tra, tránh lặp logic phân quyền ở từng dịch vụ.

Closes #12
Signed-off-by: Nguyen Van A <a@example.com>
```

Cấu hình `git config user.name` và `git config user.email` trùng với tài khoản
GitHub để commit được ghi nhận đúng người.

## 4. Pull Request

- **Mỗi PR giải quyết một Issue**, nhỏ, nên dưới khoảng 300 dòng thay đổi. Việc lớn
  thì tách Issue.
- **Mở ở trạng thái Draft** khi chưa xong hoặc CI chưa xanh; chuyển sang *Ready for
  review* khi muốn được review.
- **Tiêu đề PR theo đúng định dạng tiêu đề commit** ở mục 3. Repo merge bằng
  *Squash and merge*, nên tiêu đề PR trở thành tiêu đề commit trên `main`. CI kiểm tra
  tiêu đề PR theo Conventional Commits.
- Điền đủ mẫu PR: vì sao, cách kiểm tra, ghi chú cho người review, công cụ hỗ trợ đã
  dùng. Ghi `Closes #<số>`.
- **Rebase, không merge `main` vào nhánh.** Merge tạo commit thừa và làm lịch sử khó
  đọc:
  ```bash
  git fetch origin
  git rebase origin/main
  git push --force-with-lease
  ```
  Chỉ dùng `--force-with-lease` trên **nhánh của mình**, không bao giờ trên `main`.
  Trên GitHub có thể bấm *Update branch* và chọn *Update with rebase*.
- Cần **1 approval** và **CI xanh** mới được merge. Kiểu merge duy nhất:
  *Squash and merge*.

## 5. Quy tắc bắt buộc

- **SPDX header** ở đầu mọi tệp mã và tài liệu:
  ```
  # SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
  # SPDX-License-Identifier: Apache-2.0
  ```
  (Markdown/HTML dùng `<!-- ... -->`, JS/TS dùng `//`.) Tệp không chứa được comment
  (JSON, ảnh) kèm một tệp `<tên-tệp>.license` nằm cạnh, chứa đúng hai dòng SPDX ở
  trên không có dấu `#`, ví dụ `realm-dxlab.json.license`. Không dùng `REUSE.toml`, để
  ai mở thư mục cũng thấy giấy phép ngay. Kiểm tra bằng
  [reuse](https://reuse.software): `make check` (chạy `reuse lint`). Cài đặt:
  `pipx install reuse==6.2.0`. Trên Windows cài `pipx install "reuse[chardet]==6.2.0"`
  và đặt `REUSE_ENCODING_MODULE=chardet` trước khi chạy, vì bộ dò mặc định nhận nhầm
  tệp tiếng Việt là tệp nhị phân.
- **Không commit secret**: mật khẩu, token, API key, file `.env`. Thêm biến mới
  vào `.env.example` với giá trị giả. CI quét bằng gitleaks.
- **Thêm thư viện mới** phải bổ sung dòng tương ứng trong
  [docs/dependencies.md](docs/dependencies.md) (tên, phiên bản, giấy phép, vai trò).
  Chỉ dùng thành phần có giấy phép được OSI chấp thuận.
- **Không sửa mã nguồn của thư viện bên ngoài** trong repo.
- **Giải thích được thay đổi của mình.** Code viết cùng công cụ AI vẫn được chấp
  nhận, nhưng người mở PR phải hiểu và trình bày được nó trong mô tả PR.

## 6. Bản quyền đóng góp (DCO)

Dự án dùng [Developer Certificate of Origin 1.1](https://developercertificate.org/)
giống Keycloak, không dùng thỏa thuận chuyển giao bản quyền. Khi gửi đóng góp, bạn
xác nhận:

- Bạn là tác giả của phần đóng góp, hoặc có quyền gửi nó theo một giấy phép tương
  thích với Apache-2.0.
- Phần đóng góp được phát hành theo giấy phép của dự án (Apache-2.0), trừ khi tệp ghi
  giấy phép khác.
- Bạn hiểu rằng đóng góp và thông tin `Signed-off-by` được lưu công khai và vĩnh viễn
  trong lịch sử repo.

Bản quyền phần đóng góp vẫn thuộc về bạn. Ký xác nhận bằng cách thêm `-s` khi commit:

```bash
git commit -s
```

Git thêm dòng `Signed-off-by: Họ Tên <email>` vào cuối commit. Nếu quên, sửa commit
gần nhất bằng `git commit --amend -s` rồi `git push --force-with-lease` trên nhánh của
mình.

Mã sinh bởi công cụ AI cũng phải đáp ứng các điều trên. Ghi công cụ đã dùng trong mẫu
PR (theo Keycloak và Airflow) và chỉ gửi phần mình hiểu, giải thích được.

## 7. Review

Người review kiểm tra: đúng phạm vi Issue, chạy được, có test khi phù hợp,
có SPDX header, không lộ secret, tài liệu được cập nhật. Góp ý cụ thể, lịch sự.

## 8. Nguồn tham khảo

| Quy ước | Nguồn |
|---|---|
| Tiêu đề thể mệnh lệnh, tối đa 72 ký tự, không dấu chấm, thân giải thích vì sao, ngắt ở 72 ký tự | [Kubernetes: Commit Message Guidelines](https://github.com/kubernetes/community/blob/master/contributors/guide/pull-requests.md#commit-message-guidelines) |
| Rebase thay vì merge, squash trước khi merge | [Kubernetes: GitHub workflow](https://github.com/kubernetes/community/blob/master/contributors/guide/github-workflow.md), [Airflow: Pull Request guidelines](https://github.com/apache/airflow/blob/main/contributing-docs/05_pull_requests.rst) |
| Dòng cuối `Closes #<số>`, ký DCO bằng `--signoff`, ghi việc dùng AI | [Keycloak: CONTRIBUTING.md](https://github.com/keycloak/keycloak/blob/main/CONTRIBUTING.md) |
| Draft khi chưa đạt kiểm tra, Squash and Merge, khai công cụ AI trong mẫu PR | [Airflow: Pull Request guidelines](https://github.com/apache/airflow/blob/main/contributing-docs/05_pull_requests.rst), [Airflow: mẫu PR](https://github.com/apache/airflow/blob/main/.github/PULL_REQUEST_TEMPLATE.md) |
| Kiểm tra tiêu đề PR theo Conventional Commits trong CI | [APISIX: semantic.yml](https://github.com/apache/apisix/blob/master/.github/workflows/semantic.yml) |

Hai điểm repo này chọn khác một số dự án trên:

- Kubernetes chặn PR có `Closes #` trong commit vì từ khóa này có thể đóng nhầm Issue
  ngoài ý muốn. Repo này nhỏ, chỉ có nhánh `main`, nên theo cách của Keycloak.
- Kubernetes dùng CLA của CNCF; Keycloak dùng DCO. Repo này dùng DCO vì không có pháp
  nhân để ký CLA.
