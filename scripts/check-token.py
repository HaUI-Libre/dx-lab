#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
# SPDX-License-Identifier: Apache-2.0
"""Validate demo identity claims against the checked-in realm definition."""

import base64
import json
import pathlib
import sys
import uuid


def main():
    username = sys.argv[1]
    realm = json.loads(pathlib.Path("core/identity/realm-dxlab.json").read_text())
    defined_roles = {role["name"] for role in realm["roles"]["realm"] if role["name"].startswith("ROLE_")}
    assert defined_roles == {"ROLE_STUDENT", "ROLE_TECHNICIAN", "ROLE_LAB_MANAGER", "ROLE_ADMIN"}, "realm có thêm/thiếu role nghiệp vụ"
    ids = [str(uuid.UUID(entry["id"])) for entry in realm["users"]]
    assert len(ids) == len(set(ids)), "UUID demo trùng nhau"
    user = next(u for u in realm["users"] if u["username"] == username)
    payload = sys.stdin.read().split(".")[1]
    payload += "=" * (-len(payload) % 4)
    claims = json.loads(base64.urlsafe_b64decode(payload))
    expected_id = str(uuid.UUID(user["id"]))
    assert claims.get("sub") == expected_id, f"{username}: sai sub"
    assert claims.get("preferred_username") == username, f"{username}: sai username"
    business = {role for role in claims.get("realm_access", {}).get("roles", []) if role.startswith("ROLE_")}
    expected = {role for role in user["realmRoles"] if role.startswith("ROLE_")}
    assert business == expected and len(business) == 1, f"{username}: sai realm role nghiệp vụ"
    expected_site = user.get("attributes", {}).get("co_so", [])
    if expected_site:
        assert isinstance(claims.get("co_so"), str), f"{username}: co_so thiếu hoặc không phải chuỗi"
        assert claims["co_so"] == expected_site[0], f"{username}: sai co_so"
    else:
        assert "co_so" not in claims, f"{username}: co_so ngoài dự kiến"
    print(f"OK    token {username}: UUID, vai trò, co_so")


if __name__ == "__main__":
    try:
        main()
    except (AssertionError, KeyError, StopIteration, ValueError, IndexError) as error:
        print(f"FAIL  token {sys.argv[1]}: {error}", file=sys.stderr)
        sys.exit(1)
