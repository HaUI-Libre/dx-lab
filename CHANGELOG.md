<!--
SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
SPDX-License-Identifier: Apache-2.0
-->

# Changelog

Mọi thay đổi đáng chú ý của dự án được ghi tại đây.

Định dạng theo [Keep a Changelog](https://keepachangelog.com/vi/1.1.0/),
đánh số phiên bản theo [Semantic Versioning](https://semver.org/lang/vi/).

## [Unreleased]

### Added
- `data/pyproject.toml`, `ai/pyproject.toml`: `pip install ./data` và `pip install ./ai`
  trong venv sạch, chạy được từ thư mục bất kỳ; lệnh `dxlab-data-api`,
  `dxlab-data-migrate`, `dxlab-ai-classifier`, `dxlab-ai-train`. Dockerfile không đổi,
  vẫn cài bằng `requirements.txt` (#141).
- `ai/train.py` mặc định đọc `data/samples/training_data.jsonl` của repo khi chạy
  `python ai/train.py` từ gốc repo; báo lỗi rõ khi không thấy tệp dữ liệu, cho cả hai
  cách chạy (#141).
- CI workflow `Build from source`: job `Data API` và `Dịch vụ phân loại` cài bằng
  `pip install`, job sau còn huấn luyện lại mô hình rồi gọi `/health` và `/classify`
  ngoài `$RUNNER_TEMP`, hoàn tất job `data/` và `ai/` còn thiếu từ #154 (#148).

## [1.0.0] - 2026-10-26

### Added
- Giao diện DX-Helpdesk mới (#119): design tokens cho chế độ sáng và tối; phông tự lưu trữ
  qua @fontsource (OFL-1.1), chỉ nạp subset latin và vietnamese; tem 7 trạng thái, bảng lệnh
  Ctrl+K theo vai trò, trang `/styleguide`; danh sách phiếu dựng từng 30 phiếu, dạng khối
  trên màn hẹp mà vẫn giữ ngữ nghĩa bảng; nén sẵn JS, CSS và nén HTML do server render;
  giờ hiển thị theo `Asia/Ho_Chi_Minh` (#120).
- `GET /api/data/stats` (#22): số phiếu theo trạng thái, loại, cơ sở, giờ xử lý trung bình,
  số quá hạn so với `sla_due_at`, số lần mở lại; trưởng phòng nhận cơ sở trong claim
  `co_so` (hỏi cơ sở khác thì 403), admin xem mọi cơ sở hoặc chọn `co_so`; không tính bản
  nháp chưa gửi. Trang `/dashboard` (#27) hiện số liệu; `make smoke` so kết quả với đếm
  thẳng trên PostgreSQL cho trưởng phòng CS1, admin cả ba cơ sở và admin chọn CS2.
- Cập nhật trạng thái phiếu thời gian thực (#123): `GET /api/data/events/stream` (SSE) nhận
  `dxlab.ticket.status_changed` từ NATS, lọc từng sự kiện theo quyền đọc phiếu, ping mỗi 15
  giây, đóng khi token hết hạn; app giữ một kết nối qua `/gw`, đánh dấu dòng vừa đổi và
  hiện "Trực tiếp" hoặc "Mất kết nối cập nhật" (#125).
- Nút vào thử bằng tài khoản demo ở trang đăng nhập (#121): `/auth/login?hint=` chỉ nhận tên
  trong danh sách tài khoản demo, chỉ điền sẵn tên trên Keycloak, không đi qua mật khẩu (#126).
- Chế độ xem cột với kéo thả phiếu để chuyển bước (#124): chỉ cột hợp lệ với vai trò và bước
  BPMN mới nhận thả, mỗi lần thả gọi đúng action của Data API nên đi qua Flowable; bàn phím
  dùng nút "Chuyển"; máy chủ từ chối thì thẻ về cột cũ (#127).
- Dịch vụ phân loại `ai/` (Tầng 2, I): luật theo từ khoá tiếng Việt khi mô hình chưa có,
  lỗi hoặc quá `AI_MODEL_TIMEOUT_SECONDS`, không khớp từ khoá thì trả 422 để người dùng chọn
  tay (#30, #131); hai bộ phân loại TF-IDF và logistic regression (scikit-learn 1.7.2,
  joblib 1.5.2) cho loại sự cố và mức ưu tiên, huấn luyện lúc build image từ 160 mẫu, kết
  quả đánh giá ở `ai/EVALUATION.md` (#28, #132); CI job `AI classifier` (#132).
- `docs/build-from-source.md` (#147): build app Nuxt rồi chạy `.output` ngoài repo bằng
  Node, bảng biến `NUXT_*`; cài plugin `dxlab-roles` vào APISIX có sẵn qua
  `extra_lua_path`. Biến `PORTAL_DATA_DIR` chỉ thư mục chứa `campuses.json`, không đọc
  được thì app ghi cảnh báo; `make test-lua` chép plugin vào APISIX dựng riêng, ký token
  bằng khoá tạm, kiểm tra 401/403/200 (#153).
- CI workflow `Build from source` (#148): app build, chép ra `$RUNNER_TEMP`, xoá
  `.output` và `node_modules` trong repo rồi chạy, gọi `/healthz`; job thứ hai chạy
  `make test-lua`. Phần `data/` và `ai/` chờ #141 (#154).
- `ROADMAP.md`: bản đã phát hành và việc dự kiến sau v1.0.0, mỗi việc trỏ tới Issue;
  README và CONTRIBUTING trỏ tới danh sách Issue `good first issue` (#149, #152).
- README mục "Chạy thử": dựng bằng `make env`, `make demo`, `make seed`, tài khoản theo
  vai trò, một vòng nghiệp vụ mẫu và các nhánh khác (#134).
- CONTRIBUTING mục 7 "Đóng góp có hỗ trợ của AI": người ký DCO chịu trách nhiệm và giải
  thích được mã mình đứng tên, không đưa secret hay dữ liệu cá nhân vào công cụ AI
  (#146, #151). `AGENTS.md` có mục quy tắc cho AI agent chạy trong repo (#135, #136).
- Biên bản build từ mã nguồn trên máy sạch `docs/demo/bien-ban-build-may-sach.md`: số liệu Linux sạch lấy từ runner CI mới (`make up`, `make smoke`, `make smoke-assets`); Windows sạch qua WSL2 chưa chạy (#38).
- Kiểm thử end-to-end theo chuỗi demo tích hợp bằng `make test-e2e` (SSO, thiết bị từ Snipe-IT, báo hỏng kèm ảnh, định tuyến và chặn chéo cơ sở, phân công, nhãn Snipe-IT qua NATS, biên bản, mở lại, nghiệm thu và hoàn trả nhãn, đánh giá, provenance, từ chối, phiếu không có asset_id). Gợi ý phân loại và thống kê được đánh dấu bỏ qua cho tới khi #28, #30, #31 và #22 xong; biên bản 2 lần chạy tại `docs/demo/bien-ban-test-e2e.md` (#34).
- `docs/testing.md` (các lớp kiểm thử và CI, #33), `docs/audit.md` (rà giấy phép từng tệp và
  secret toàn lịch sử, #37), `docs/manual-checks.md` (việc cần kiểm tra bằng tay); README có
  bảng tính năng, tích hợp tài sản, chuẩn mở, cấu hình và lệnh kiểm tra (#35);
  `docs/architecture.md` thêm mục chuẩn mở.
- Giám sát trong profile `monitoring` (#78): Prometheus 3.15.0 thu metric từ APISIX (plugin
  `prometheus`), Keycloak, PostgreSQL (`postgres_exporter`, role `pg_monitor`), Data API,
  `asset-sync` và NATS; Grafana 13.2.4 ở `127.0.0.1:3001` với dashboard nạp qua provisioning;
  `make smoke-monitoring`. Flowable REST 7.2.0 không có endpoint Prometheus, đã ghi kết quả.
- Trang `/dashboard` cho trưởng phòng và admin (#27): tổng ticket, giờ xử lý trung bình, số quá
  hạn, số lần mở lại, biểu đồ theo trạng thái, loại và cơ sở từ `GET /api/data/stats`; admin
  lọc theo cơ sở; khi API thống kê (#22) chưa có thì trang ghi rõ.
- Form báo hỏng gọi `POST /api/ai/classify` khi mô tả đủ dài, hiện loại và mức ưu tiên gợi
  ý kèm từ khoá và nguồn (mô hình hay luật); chỉ áp dụng khi người dùng bấm "Dùng gợi ý";
  dịch vụ phân loại chưa chạy thì form vẫn gửi được (#32).
- NATS JetStream 2.15.1 trong profile `integration` (#77): Data API phát
  `dxlab.ticket.status_changed` sau khi commit, `asset-sync` nhận bằng durable consumer nên
  sự kiện lúc dịch vụ dừng không mất; không có NATS thì quay về lời gọi trực tiếp.
  `make smoke-assets` thử đóng ticket khi `asset-sync` dừng rồi bật lại.
- Dựng Snipe-IT (v8.8.0) và MariaDB (11.4.7) trong profile `integration` của Docker Compose; kịch bản tự động khởi tạo admin, nạp dữ liệu mẫu 3 cơ sở từ `data/samples/snipeit_seed.json`, cấp API token và đồng bộ vào `.env`; lệnh `make snipeit-token` (#71).
- CI job `Python tests` chạy `pytest` trên `tests/`; `make test` chạy cùng bộ test trên máy.
- Giao diện báo hỏng và quy trình (#26): `/tickets` (yêu cầu của tôi, việc được giao, hàng
  đợi theo cơ sở), `/tickets/new` (thiết bị của tôi hoặc vị trí nhập tay khi hệ thống tài
  sản tắt, kèm ảnh), `/tickets/{id}` (lịch sử, tiếp nhận, từ chối, phân công kỹ thuật viên
  cùng cơ sở, nhận việc, hoàn thành, nghiệm thu, mở lại, đánh giá); `make smoke` kiểm tra
  các trang bằng phiên đăng nhập thật.
- CI job `Stack từ volume trống (make up, make smoke)` dựng toàn bộ stack trên runner sạch
  cho PR chạm hạ tầng, chạy `make smoke` và ba nhánh BPMN qua gateway (#90).
- Data API: `GET /locations`, `GET /technicians` (kỹ thuật viên cùng cơ sở với trưởng
  phòng), đăng ký và liệt kê tệp đính kèm theo `openapi.yaml`; `submit` không còn bắt buộc
  `asset_id` để báo hỏng được khi hệ thống tài sản tắt (#26).
- Compose chia profile: mặc định (lõi và dịch vụ của đội), `integration`, `monitoring`,
  `setup` (workflow-deploy); `make demo` bật mọi profile, `make down` và `make ps` gồm cả
  service của các profile (#75).
- Cổng thông tin [H] (`/portal`): xem hồ sơ cá nhân, nhóm và đơn vị 3 cơ sở, danh sách tài liệu hướng dẫn theo vai trò người dùng, tải lên, xem và tải về qua `/api/files` kết nối SeaweedFS (#25).
- Init container `workflow-deploy` deploy BPMN qua REST nội bộ khi `make up`, chỉ tạo
  version mới khi nội dung BPMN đổi; route workflow kiểm thử chỉ cho `ROLE_ADMIN`;
  `docs/workflow-api.sh` chạy ba nhánh hoàn thành, từ chối, mở lại qua gateway (#88).
- Realm demo: user attribute `co_so` chỉ admin sửa, mapper đưa vào claim `co_so` của
  access token; 10 tài khoản demo cho 3 cơ sở với UUID cố định; `make smoke` kiểm tra
  UUID, vai trò và `co_so` của từng tài khoản (#87).
- BPMN `dxlabHelpdeskRepair` trong `core/workflow/`: tiếp nhận, phân công, xử lý,
  nghiệm thu, nhánh từ chối và mở lại bắt buộc có lý do; sơ đồ
  `docs/images/helpdesk-workflow.svg` (#85).
- Dữ liệu mẫu 3 cơ sở HaUI trong `data/samples/`: cây vị trí, tài sản và người dùng cho
  Snipe-IT, ticket ở đủ trạng thái kèm lịch sử, 160 mẫu huấn luyện phân loại;
  `make seed` nạp lặp an toàn và thoát mã lỗi khi thất bại (#81, #83).
- Ứng dụng DX-Helpdesk (Nuxt 4.5.2) trong `app/`: đăng nhập, đăng xuất SSO theo mô hình
  BFF (server Nuxt giữ token, trình duyệt chỉ có cookie phiên), trang tài khoản hiện
  tên, vai trò, cơ sở lấy qua `GET /api/me`; Dockerfile, service `app` trong compose,
  `make smoke` có bước đăng nhập qua app (#24).
- `docs/architecture.md`: tích hợp hệ thống tài sản của khách hàng (Snipe-IT), trục sự
  kiện NATS, định tuyến theo cơ sở, giám sát, profile Compose, bảng ánh xạ 7 lớp công
  nghệ của đề; ảnh `docs/images/integration-architecture.svg` (#67).
- `docs/usecases.md`: kịch bản theo hướng tích hợp tài sản, cơ sở `co_so`, nhánh mở lại
  ở bước nghiệm thu (#67).
- `CODE_OF_CONDUCT.md` theo Contributor Covenant 2.1 bản tiếng Việt (CC-BY-4.0) (#63).
- CONTRIBUTING: quy tắc viết commit, quy trình PR (Draft, rebase, squash), mục bản quyền
  đóng góp theo DCO, nguồn tham khảo từ Kubernetes, Keycloak, APISIX, Airflow (#63).
- Mẫu PR: mục "Ghi chú cho người review" và "Công cụ hỗ trợ đã dùng" (#63).
- CI kiểm tra tiêu đề PR theo Conventional Commits (#63).
- `docs/license-decision.md`: lý do chọn Apache-2.0, quyền và nghĩa vụ người dùng,
  rà soát giấy phép từng thành phần theo phiên bản kèm nguồn (#61).
- `NOTICE` theo chuẩn Apache-2.0, có phần tiếng Việt và bảng thành phần bên thứ ba (#61).
- `LICENSES/Apache-2.0.txt` theo REUSE Specification 3.3; tệp `.license` đi kèm cho
  ảnh SVG trong `docs/images/` (#61).
- README: mục Giấy phép nêu mục đích giấy phép; hướng dẫn chạy trên Windows qua WSL2 (#61).

### Changed
- Tài liệu sản phẩm (README, NOTICE, `docs/architecture.md`, `docs/usecases.md`,
  `docs/license-decision.md`, mẫu PR) mô tả phần mềm, không viết theo giọng bài dự thi;
  README thêm mục "Bối cảnh" (#135, #136).
- Service `ai` chạy trong profile mặc định của Compose; route `/api/ai/classify` của
  gateway nối tới upstream thật, giữ xác thực Keycloak; `make smoke` kiểm tra 401 khi thiếu
  token và gợi ý hợp lệ khi có token (#31, #133).
- Biến cấu hình mới `DEMO_LOGIN_HINTS` (mặc định `false` trong `.env.example`, `make demo`
  bật) và `AI_MODEL_TIMEOUT_SECONDS` (#126, #131).
- `data/openapi.yaml` thêm `GET /events/stream`; README thêm phần xử lý sự cố, gồm lỗi 502
  sau khi build lại một container (#125, #126).
- Dữ liệu mẫu seed đồng bộ với realm Keycloak (#84): Thay thế username thành UUID cố định của người dùng trong Keycloak realm cho các trường `created_by`, `assigned_to` trong `tickets_seed.sql` và `tickets.json`, `created_by` trong `ticket_attachments`, cùng `actor_sub` và `technician_sub` trong `ticket_events`; đồng bộ danh sách username và email trong `snipeit_seed.json`; giúp Data API lọc chính xác hàng đợi ticket theo token claim `sub` và `co_so` cho cả 3 cơ sở.
- `docs/dependencies.md`, `docs/license-decision.md` khớp với compose (#36): NATS, Prometheus,
  Grafana và exporter chuyển sang "đang dùng"; thêm thư viện Python của Data API và
  `asset-sync` với giấy phép đọc tại đúng tag; sửa phiên bản FastAPI (0.141.1).
- Data API tra người dùng Keycloak bằng service account `dxlab-data-api` (client credentials,
  chỉ `view-users`) thay cho tài khoản admin realm `master`; `KEYCLOAK_ADMIN` và
  `KEYCLOAK_ADMIN_PASSWORD` không còn được truyền vào container `data-api`.
- `docs/workflow-api.sh` và `.py` chuyển thành `scripts/test-workflow-api.sh` và `.py`;
  `docs/workflow-api.md` giữ hướng dẫn.
- PostgreSQL chạy bằng image `postgis/postgis:18-3.6-alpine` ghim digest (PostgreSQL 18.6,
  PostGIS 3.6.4); extension `postgis` bật trên `dxdata` khi khởi tạo; `make smoke` kiểm tra
  `postgis_lib_version()` (#76).
- Cập nhật cách diễn đạt về phạm vi áp dụng giấy phép và bảng tham chiếu công nghệ trong tài liệu (#92).
- CI và `make check` kiểm tra giấy phép bằng `reuse lint` thay cho
  `scripts/check_spdx.sh` (#61).
- `docs/dependencies.md`: thêm cột "Cách dùng", thành phần dự kiến của hướng tích hợp
  tài sản, danh sách đã cân nhắc nhưng không dùng (#61).
- README yêu cầu Docker Engine và Compose plugin, không cần Docker Desktop (#61).
- Redirect URI của client `dxlab-app` và CORS ở gateway lấy theo `APP_PORT`, không ghim
  `localhost:3000` (#24).
- `/api/me` trả thêm `co_so` khi token có claim này (#24).

### Removed
- RAG, Ollama, pgvector khỏi phạm vi; bỏ `OLLAMA_MODEL`, `AI_FALLBACK_RULE_BASED`
  khỏi `.env.example` (#61).
- `scripts/check_spdx.sh` (#61).

### Fixed
- Data API không gọi được Flowable: `DATA_WORKFLOW_KEY` chưa có trong `nginx_config.envs`
  của APISIX nên route `workflow-data` luôn trả 403 và mọi bước chuyển trạng thái trả 503.
  `make env` sinh khoá ngẫu nhiên thay cho `changeme` (trừ mật khẩu tài khoản demo);
  `make up` dừng khi `DATA_WORKFLOW_KEY` còn là `changeme`; `make smoke` chạy vòng đời
  ticket qua Data API, gồm nhánh mở lại và từ chối (#98).
- Gateway kiểm tra quyền theo đường dẫn trong `/api/files`: `guides/admin/` chỉ admin đọc,
  `guides/technician/` chỉ kỹ thuật viên, quản lý, admin đọc; ghi và xoá `guides/`, `portal/`
  chỉ quản lý và admin. Trước đây mọi vai trò đọc, ghi được mọi tệp, kể cả metadata phân
  quyền của portal. Chặn `..` và `%2e` trong request gốc (#95).
- Keycloak 26.8 không import được realm trên volume trống vì user profile đặt
  `unmanagedAttributePolicy` là `DISABLED`, giá trị không hợp lệ; bỏ trường này (#89).
- `docs/workflow-api.sh` lỗi khi sắp xếp lịch sử task vì Flowable 7 sinh ID task dạng
  UUID; sắp xếp theo thời gian bắt đầu và kết thúc (#89).
- Gateway trả `Content-Type: application/json` cho `/api/me` và các lỗi 400, 403, 503
  do gateway tự sinh; trước đây là `text/plain` (#24).

## [0.1.0] - 2026-10-14

### Added
- Khung repository: cấu trúc thư mục, README, CONTRIBUTING, CHANGELOG.
- Mẫu Issue/Pull Request, CODEOWNERS.
- CI: kiểm tra SPDX header và quét secret bằng gitleaks.
- `.env.example`, Makefile, bảng dependency/license.
- `docs/usecases.md`: đặc tả nghiệp vụ DX-Helpdesk (vai trò, loại sự cố, trạng thái,
  kịch bản), chuyển từ bản .docx (#9).
- Docker Compose: PostgreSQL 18 với volume, healthcheck và script tạo database
  riêng cho Keycloak, Flowable, Data API (#11).
- Keycloak 26.8: realm `dxlab` tự import, client OIDC `dxlab-app`, 4 realm role
  theo M1.3 và tài khoản demo cho mỗi vai trò; mật khẩu lấy từ `.env` (#12).
- APISIX 3.19 chạy standalone: route `/api/me`, `/api/data`, `/api/workflow`,
  `/api/files`, `/api/ai`; xác thực token Keycloak bằng JWKS, plugin `dxlab-roles`
  kiểm tra vai trò; `make smoke` kiểm tra 401/200/403 (#13).
- `docs/architecture.md`: kiến trúc 3 tầng, ánh xạ không gian H-P-D-I, ranh giới mạng,
  6 luồng gọi dịch vụ (sequence diagram), bảng hợp đồng API và 5 quyết định kiến trúc
  then chốt (ADR); bổ sung ảnh sơ đồ vector trong `docs/images/` (#10).
- SeaweedFS 4.48 lưu tệp trong bucket `documents`; tải lên/tải về qua
  `/api/files` của gateway, chặn liệt kê thư mục và lệnh quản trị của filer (#14).
- Flowable REST chạy headless trên database `flowable`; gateway công bố
  `GET /api/workflow/repository/process-definitions` (#15).
- `data/schema.sql` và `data/openapi.yaml`: schema ticket, tệp đính kèm, lịch sử và
  hợp đồng Data API dự kiến (#16).

### Changed
- CI dùng `actions/checkout@v5` và ghim `ubuntu-24.04`.

[Unreleased]: https://github.com/HaUI-Libre/dx-lab/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/HaUI-Libre/dx-lab/compare/v0.1.0...v1.0.0
[0.1.0]: https://github.com/HaUI-Libre/dx-lab/releases/tag/v0.1.0

