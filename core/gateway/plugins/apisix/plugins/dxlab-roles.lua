-- SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
-- SPDX-License-Identifier: Apache-2.0
--
-- Kiểm tra realm role của Keycloak sau khi openid-connect đã xác thực token.
-- Trả 403 nếu token không có vai trò nào trong danh sách `roles` của route,
-- rồi chuyển thông tin người dùng xuống upstream qua X-User-Id, X-User-Name, X-User-Roles.
--
-- Plugin đọc payload JWT từ header X-Userinfo do openid-connect đặt (header client
-- tự gửi bị openid-connect xoá trước đó), nên route phải bật cả openid-connect.

local core = require("apisix.core")
local ngx  = ngx

local plugin_name = "dxlab-roles"

local schema = {
    type = "object",
    properties = {
        roles = {
            type = "array",
            items = { type = "string" },
            minItems = 1,
            uniqueItems = true,
        },
    },
    required = { "roles" },
}

local _M = {
    version  = 0.1,
    -- Ngay sau openid-connect (2599) trong pha rewrite
    priority = 2590,
    name     = plugin_name,
    schema   = schema,
}

function _M.check_schema(conf)
    return core.schema.check(schema, conf)
end

local function has_openid_connect(ctx)
    local plugins = ctx.plugins or {}
    for i = 1, #plugins, 2 do
        if plugins[i].name == "openid-connect" then
            return true
        end
    end
    return false
end

local function forbidden(message)
    return 403, { error = "forbidden", message = message }
end

function _M.rewrite(conf, ctx)
    for _, h in ipairs({ "X-User-Id", "X-User-Name", "X-User-Roles" }) do
        core.request.set_header(ctx, h, nil)
    end

    if not has_openid_connect(ctx) then
        core.log.error(plugin_name, " cần openid-connect trên cùng route")
        return 500, { error = "gateway misconfigured" }
    end

    local encoded = core.request.header(ctx, "X-Userinfo")
    local raw = encoded and ngx.decode_base64(encoded)
    local claims = raw and core.json.decode(raw)
    if type(claims) ~= "table" then
        return forbidden("không đọc được thông tin token")
    end

    local token_roles = claims.realm_access and claims.realm_access.roles
    if type(token_roles) ~= "table" then
        token_roles = {}
    end

    local granted = {}
    for _, role in ipairs(token_roles) do
        granted[role] = true
    end

    local allowed = false
    for _, role in ipairs(conf.roles) do
        if granted[role] then
            allowed = true
            break
        end
    end
    if not allowed then
        return forbidden("cần một trong các vai trò: " .. table.concat(conf.roles, ", "))
    end

    core.request.set_header(ctx, "X-User-Id", claims.sub)
    core.request.set_header(ctx, "X-User-Name", claims.preferred_username)
    core.request.set_header(ctx, "X-User-Roles", table.concat(token_roles, ","))
end

return _M
