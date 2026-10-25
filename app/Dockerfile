# SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
# SPDX-License-Identifier: Apache-2.0
#
# Dựng từ mã nguồn: `docker compose build app`. Bản chạy chỉ chứa .output,
# là thư mục Nitro tự gom mã server và đúng các gói npm cần lúc chạy.

FROM node:24.21.0-alpine AS build
WORKDIR /src
COPY app/package.json app/package-lock.json ./
# Cài đúng phiên bản trong lockfile; script postinstall (nuxt prepare) chạy ở bước build
RUN npm ci --ignore-scripts --no-audit --no-fund
COPY app/ .
RUN npm run build

FROM node:24.21.0-alpine
WORKDIR /app
ENV NODE_ENV=production \
    HOST=0.0.0.0 \
    PORT=3000
COPY --from=build --chown=node:node /src/.output ./.output
COPY --chown=node:node data/samples/campuses.json ./data/samples/campuses.json
# OFL-1.1 yêu cầu bản phân phối phông kèm thông báo bản quyền và giấy phép
COPY --from=build /src/node_modules/@fontsource/be-vietnam-pro/LICENSE ./licenses/be-vietnam-pro-OFL.txt
COPY --from=build /src/node_modules/@fontsource-variable/nunito/LICENSE ./licenses/nunito-OFL.txt
COPY --from=build /src/node_modules/@fontsource-variable/jetbrains-mono/LICENSE ./licenses/jetbrains-mono-OFL.txt
USER node
EXPOSE 3000
HEALTHCHECK --interval=10s --timeout=5s --start-period=10s --retries=10 \
  CMD wget -qO /dev/null http://127.0.0.1:3000/healthz || exit 1
CMD ["node", ".output/server/index.mjs"]
