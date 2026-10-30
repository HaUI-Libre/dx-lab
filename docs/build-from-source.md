<!--
SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
SPDX-License-Identifier: Apache-2.0
-->

# Build và cài từ mã nguồn không dùng Docker

`make up` dựng mọi thứ bằng Docker. Tài liệu này dành cho người muốn build mã của đội
từ mã nguồn rồi chạy bên ngoài thư mục repo, hoặc gắn vào một hạ tầng đã có sẵn.

| Phần | Tài liệu |
|---|---|
| Ứng dụng DX-Helpdesk (Nuxt, `app/`) | Mục 1 |
| Plugin `dxlab-roles` cho APISIX (`core/gateway/plugins/`) | Mục 2 |
| Data API (`data/`), dịch vụ phân loại (`ai/`) | Mục 3 |
| Dịch vụ tích hợp tài sản `asset-sync` (`integration/assets/`) | Mục 4 |

Các service còn lại (Keycloak, APISIX, PostgreSQL, Flowable, SeaweedFS, NATS, Snipe-IT)
là thành phần nguồn mở chạy riêng. Ví dụ bên dưới dùng chúng từ `make up` hoặc `make demo`.

Mọi lệnh chạy từ gốc repo trừ khi có `cd`. Trên Windows, chạy trong WSL2 như hướng dẫn
trong README; lệnh giữ nguyên.

## 1. Ứng dụng DX-Helpdesk

### Yêu cầu

- Node.js 24 LTS (`engines` trong `app/package.json`: `>=24.11.0 <25`) và npm đi kèm.
- Keycloak và APISIX đang chạy, ví dụ bằng `make up`. Nếu app trong compose đang chạy,
  dừng nó để nhường cổng: `docker compose stop app`.

### Cấu hình

Không biến nào cần có lúc build. Giá trị trong `app/nuxt.config.ts` là mặc định; biến
`NUXT_*` ghi đè lúc chạy, nên một bản build dùng được cho nhiều môi trường.

| Biến | Mặc định | Ý nghĩa |
|---|---|---|
| `NUXT_APP_URL` | `http://localhost:3000` | Địa chỉ app mà trình duyệt thấy, dùng tạo `redirect_uri`. Phải khớp redirect URI của client trong realm (`http://localhost:<APP_PORT>/*`) |
| `NUXT_OIDC_ISSUER_INTERNAL` | `http://localhost:8080/realms/dxlab` | Server app đọc discovery và đổi code lấy token ở địa chỉ này |
| `NUXT_OIDC_CLIENT_ID` | `dxlab-app` | Client OIDC |
| `NUXT_OIDC_CLIENT_SECRET` | rỗng, bắt buộc | Client secret, cùng giá trị `KEYCLOAK_CLIENT_SECRET` trong `.env` |
| `NUXT_SESSION_PASSWORD` | rỗng, bắt buộc | Khoá mã hoá cookie phiên, ít nhất 32 ký tự (`openssl rand -hex 32`) |
| `NUXT_GATEWAY_URL` | `http://localhost:9080` | APISIX; mọi lời gọi API đi qua đây |
| `NUXT_PUBLIC_DEMO_LOGIN` | `false` | Hiện nút vào thử bằng tài khoản demo |
| `PORTAL_DATA_DIR` | dò theo thư mục hiện tại | Thư mục chứa `campuses.json` cho trang portal |
| `HOST`, `PORT` | `PORT=3000` | Địa chỉ và cổng server lắng nghe |

Không đọc được `campuses.json` thì server ghi cảnh báo kèm các đường dẫn đã thử, và
portal dùng địa chỉ cơ sở ghi sẵn trong mã.

### Build

```bash
cd app
npm ci          # đúng phiên bản trong package-lock.json
npm run build   # tạo app/.output
```

`.output` là bản chạy hoàn chỉnh: Nitro gom mã server và đúng các gói npm cần lúc chạy,
không cần `node_modules` hay mã nguồn.

### Cài và chạy ngoài repo

```bash
DEST=$HOME/dx-helpdesk
mkdir -p "$DEST/data"
cp -r app/.output "$DEST/"
cp data/samples/campuses.json "$DEST/data/"

cd "$DEST"
NUXT_OIDC_CLIENT_SECRET=<KEYCLOAK_CLIENT_SECRET> \
NUXT_SESSION_PASSWORD=<APP_SESSION_PASSWORD> \
PORTAL_DATA_DIR="$DEST/data" \
node .output/server/index.mjs
```

Kiểm tra:

```bash
curl -s -o /dev/null -w '%{http_code}\n' http://localhost:3000/healthz   # 200
```

Mở http://localhost:3000, đăng nhập bằng một tài khoản demo (mục "Tài khoản demo" trong
README), rồi mở `/portal`.

Phiên đăng nhập lưu trong bộ nhớ server: khởi động lại tiến trình thì người dùng đăng
nhập lại. Chạy lâu dài thì đặt tiến trình dưới trình quản lý dịch vụ của hệ điều hành
(ví dụ systemd) với cùng các biến trên.

## 2. Plugin `dxlab-roles` vào APISIX có sẵn

Plugin kiểm tra realm role trong token Keycloak sau khi `openid-connect` đã xác thực,
trả 403 khi thiếu vai trò, rồi chuyển `X-User-Id`, `X-User-Name`, `X-User-Roles` xuống
upstream. Header cùng tên do client gửi bị xoá. Route có `dxlab-roles` mà thiếu
`openid-connect` thì trả 500.

### Yêu cầu

- APISIX 3.x. Đội dùng 3.19.0.
- Plugin `openid-connect` bật trên cùng route.

### Các bước

1. **Chép plugin.** Tên module là `apisix.plugins.dxlab-roles`, nên tệp phải nằm trong
   `apisix/plugins/` dưới thư mục khai báo ở bước 2:

   ```bash
   sudo install -D -m 0644 core/gateway/plugins/apisix/plugins/dxlab-roles.lua \
     /opt/dxlab/apisix/plugins/dxlab-roles.lua
   ```

2. **Khai báo trong `config.yaml`** của APISIX (bản cài từ gói: `/usr/local/apisix/conf/config.yaml`):

   ```yaml
   apisix:
     extra_lua_path: "/opt/dxlab/?.lua"
   plugins:
     # Danh sách này thay hẳn danh sách mặc định: giữ mọi plugin đang dùng, thêm dxlab-roles
     - openid-connect
     - dxlab-roles
   ```

3. **Khởi động lại APISIX**, vì `config.yaml` chỉ được đọc lúc khởi động: `apisix restart`,
   hoặc `sudo systemctl restart apisix` với bản cài từ gói.

4. **Gắn vào route**, cùng `openid-connect`. Ví dụ ở chế độ standalone (`apisix.yaml`):

   ```yaml
   routes:
     - uri: /api/data/*
       plugins:
         openid-connect:
           client_id: dxlab-app
           discovery: http://keycloak:8080/realms/dxlab/.well-known/openid-configuration
           bearer_only: true
           use_jwks: true
           set_userinfo_header: true
         dxlab-roles:
           roles: [ROLE_LAB_MANAGER, ROLE_ADMIN]
       upstream:
         type: roundrobin
         nodes:
           "data-api:8000": 1
   #END
   ```

   Cấu hình đầy đủ của đội ở `core/gateway/apisix.yaml`; giải thích ở
   `core/gateway/README.md`.

5. **Kiểm tra:** không có token thì 401, token thiếu vai trò thì 403, token đủ vai trò
   thì 200.

### Kiểm tra tự động

`make test-lua` chạy `scripts/test-lua-plugin.sh`. Script làm đúng các bước trên với một
APISIX dựng riêng, cần Docker và `openssl`, không cần stack hay `.env`:

1. Tạo container từ image chính thức `apache/apisix:3.19.0-debian`. Đổi phiên bản bằng
   `APISIX_IMAGE`.
2. Chép plugin vào, không mount thư mục repo.
3. Ký token bằng một khoá RSA tạm.
4. Kiểm tra 5 trường hợp:
   - Không có token: 401.
   - Có `X-Userinfo` tự gửi nhưng không có token: 401.
   - Token ký bằng khoá khác: 401.
   - Token đúng nhưng sai vai trò: 403.
   - Token đúng, đúng vai trò: 200.

## 3. Data API và dịch vụ phân loại

`data/pyproject.toml` và `ai/pyproject.toml` cho phép `pip install ./data` và
`pip install ./ai` trong một venv, không cần Docker. Image Docker vẫn cài bằng
`requirements.txt` như trước (không đổi, giữ cache layer); `pyproject.toml` chỉ phục vụ
cách chạy này.

### Yêu cầu

- Python 3.12+.
- Keycloak và APISIX đang chạy nếu muốn gọi Data API qua gateway với token thật.
  Chỉ gọi `/health` thì không cần dịch vụ nào khác.

### Data API

```bash
VENV_DATA=$HOME/.venvs/dxlab-data      # đường dẫn tuyệt đối, dùng được sau khi cd
python3 -m venv "$VENV_DATA"
"$VENV_DATA/bin/pip" install ./data

cd /thư-mục-ngoài-repo
"$VENV_DATA/bin/dxlab-data-api"        # lắng nghe cổng 8000 (biến PORT đổi được)
```

`/health` trả `{"status": "ok"}` ngay, không chạm PostgreSQL. Các route khác cần
`DATA_DB_PASSWORD` và các biến `KEYCLOAK_*`, `DATA_WORKFLOW_*` như khi chạy bằng Docker
(xem [data/README.md](../data/README.md)).

Áp dụng schema/migration cho một PostgreSQL đã chạy. **PostGIS 3.x là phụ thuộc bắt
buộc** (định tuyến theo cơ sở, #79): cài gói PostGIS 3 cho bản PostgreSQL đang dùng, rồi
bật extension trên `dxdata` bằng tài khoản superuser, vì PostGIS không phải extension
"trusted" nên user `dxdata` không tự tạo được:

```bash
sudo -u postgres psql -d dxdata -c 'CREATE EXTENSION IF NOT EXISTS postgis'
DATA_DB_HOST=<host> DATA_DB_PASSWORD=<mật khẩu> "$VENV_DATA/bin/dxlab-data-migrate"
```

Thiếu PostGIS thì `dxlab-data-migrate` dừng trước khi đổi schema với thông báo "Data API
cần PostGIS 3.x trên database dxdata" kèm lỗi gốc. Stack Docker bật sẵn extension bằng
`core/postgres/init/02-enable-postgis.sh`.

### Dịch vụ phân loại (`ai/`)

```bash
VENV_AI=$HOME/.venvs/dxlab-ai
python3 -m venv "$VENV_AI"
"$VENV_AI/bin/pip" install ./ai

# Huấn luyện: mặc định đọc data/samples/training_data.jsonl của repo khi chạy
# "python ai/train.py" từ gốc repo; bản đã cài phải truyền --data vì không còn ở
# trong repo để tự dò
mkdir -p "$HOME/dx-ai"
"$VENV_AI/bin/dxlab-ai-train" --data data/samples/training_data.jsonl --output "$HOME/dx-ai/model.joblib"

cd /thư-mục-ngoài-repo
AI_MODEL_PATH="$HOME/dx-ai/model.joblib" "$VENV_AI/bin/dxlab-ai-classifier"
```

Không đặt `AI_MODEL_PATH` thì dịch vụ dùng mặc định `/service/model.joblib` (đường dẫn
trong image Docker) và mọi lời gọi `/classify` rơi về luật từ khóa (`source: "rules"`),
trả 422 khi không khớp từ khóa nào — không phải lỗi, nhưng cần đặt biến để dùng mô hình
đã huấn luyện. `/health` luôn trả `{"status": "ok"}` kể cả khi chưa có mô hình.

### Kiểm tra tự động

CI job `Build from source` có hai job `Data API` và `Dịch vụ phân loại`: mỗi job tạo venv
riêng, `pip install` từ thư mục repo, chạy ngoài `$RUNNER_TEMP`. Job Data API chỉ gọi
`/health`. Job phân loại huấn luyện bằng `dxlab-ai-train`, ghi mô hình ra `$RUNNER_TEMP`,
rồi gọi `/health` và `/classify` với một câu khớp luật dự phòng để không phụ thuộc thời
gian nạp mô hình lần đầu trên máy CI.

## 4. Dịch vụ tích hợp tài sản `asset-sync`

`integration/assets/` chưa có `pyproject.toml`; cài bằng `requirements.txt` như image
Docker rồi chép hai tệp mã (`app.py`, `adapter.py`) ra thư mục cài.

### Yêu cầu

- Python 3.12+.
- Snipe-IT có API token (`make demo` rồi `make snipeit-token`), Keycloak đang chạy. NATS
  không bắt buộc: không đặt `NATS_URL` thì dịch vụ chỉ nhận lời gọi trực tiếp từ Data API.

### Cấu hình

Đặt trước khi chạy; tên biến giống service `asset-sync` trong `docker-compose.yml`:

| Biến | Ý nghĩa |
|---|---|
| `SNIPEIT_API_URL` | REST API Snipe-IT, ví dụ `http://127.0.0.1:8081/api/v1` |
| `SNIPEIT_TOKEN_FILE` | Tệp chứa API token Snipe-IT |
| `ASSET_STATE_DB` | Tệp SQLite lưu nhãn ban đầu và hàng thử lại; mặc định `/state/...` chỉ đúng trong image |
| `DATA_ASSET_KEY` | Cùng giá trị trong `.env`, Data API gửi khi cập nhật nhãn |
| `KEYCLOAK_ISSUER`, `KEYCLOAK_JWKS_URL`, `KEYCLOAK_CLIENT_ID` | Kiểm tra token người dùng |
| `NATS_URL`, `ASSET_REPAIR_LABEL`, `ASSET_SITE_ROOTS` | Tùy chọn, xem README mục Cấu hình |

### Build, cài và chạy ngoài repo

```bash
VENV_ASSETS=$HOME/.venvs/dxlab-assets
DEST=$HOME/dx-asset-sync
python3 -m venv "$VENV_ASSETS"
"$VENV_ASSETS/bin/pip" install -r integration/assets/requirements.txt
mkdir -p "$DEST/state"
cp integration/assets/app.py integration/assets/adapter.py "$DEST/"
make snipeit-token > "$DEST/snipeit_api_token"

cd "$DEST"
SNIPEIT_API_URL=http://127.0.0.1:8081/api/v1 \
SNIPEIT_TOKEN_FILE="$DEST/snipeit_api_token" \
ASSET_STATE_DB="$DEST/state/updates.sqlite3" \
DATA_ASSET_KEY=<DATA_ASSET_KEY> \
KEYCLOAK_ISSUER=http://localhost:8080/realms/dxlab \
KEYCLOAK_JWKS_URL=http://localhost:8080/realms/dxlab/protocol/openid-connect/certs \
"$VENV_ASSETS/bin/uvicorn" --app-dir "$DEST" app:app --port 8002
```

`curl http://localhost:8002/health` trả `{"status": "ok", ...}`. Dịch vụ mở thêm cổng
metric 9100 (`METRICS_PORT`). Data API gọi dịch vụ qua gateway (`DATA_ASSET_URL`,
`DATA_ASSET_STATUS_URL` mặc định trỏ vào APISIX), nên để dùng bản này thay cho container
chỉ cần trỏ upstream các route `/api/assets` trong `core/gateway/apisix.yaml` về địa chỉ
trên. Bước này chưa có job CI kiểm chứng.
