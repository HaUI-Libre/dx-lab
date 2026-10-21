#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
# SPDX-License-Identifier: Apache-2.0
"""Script nạp dữ liệu mẫu 3 cơ sở HaUI vào PostgreSQL (dxdata)."""

from __future__ import annotations

import argparse
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request

# Đảm bảo in ký tự tiếng Việt an toàn trên console Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, io.UnsupportedOperation) as exc:
        print(f"Cảnh báo cấu hình stdout: {exc}", file=sys.stderr)
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, io.UnsupportedOperation) as exc:
        print(f"Cảnh báo cấu hình stderr: {exc}", file=sys.stderr)

REPO_ROOT = Path(__file__).resolve().parent.parent
SAMPLES_DIR = REPO_ROOT / "data" / "samples"


def load_env_file(env_path: Path) -> dict[str, str]:
    """Đọc file .env nếu tồn tại để lấy cấu hình kết nối."""
    env_vars: dict[str, str] = {}
    if not env_path.exists():
        return env_vars
    try:
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                env_vars[k.strip()] = v.strip().strip("\"'")
    except OSError as err:
        print(f"Lỗi đọc file .env: {err}", file=sys.stderr)
    return env_vars


def validate_samples() -> bool:
    """Kiểm tra cú pháp và tính toàn vẹn của tất cả các tệp dữ liệu mẫu."""
    campuses_file = SAMPLES_DIR / "campuses.json"
    guides_file = SAMPLES_DIR / "guides.json"
    snipeit_file = SAMPLES_DIR / "snipeit_seed.json"
    tickets_json = SAMPLES_DIR / "tickets.json"
    tickets_sql = SAMPLES_DIR / "tickets_seed.sql"
    training_file = SAMPLES_DIR / "training_data.jsonl"

    files_to_check = [campuses_file, guides_file, snipeit_file, tickets_json, tickets_sql, training_file]
    missing = [f.name for f in files_to_check if not f.exists()]
    if missing:
        print(f"Thiếu các tệp dữ liệu mẫu: {missing}", file=sys.stderr)
        return False

    try:
        with open(campuses_file, "r", encoding="utf-8") as f:
            json.load(f)
        with open(guides_file, "r", encoding="utf-8") as f:
            json.load(f)
        with open(snipeit_file, "r", encoding="utf-8") as f:
            json.load(f)
        with open(tickets_json, "r", encoding="utf-8") as f:
            json.load(f)
        with open(training_file, "r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, 1):
                if line.strip():
                    json.loads(line)
    except (json.JSONDecodeError, OSError) as err:
        print(f"Lỗi cú pháp tệp dữ liệu mẫu: {err}", file=sys.stderr)
        return False

    return True


def run_psql(args: list[str], input_data: str | None = None) -> tuple[int, str, str]:
    """Chạy psql qua docker compose exec hoặc psql cài cục bộ."""
    env_vars = load_env_file(REPO_ROOT / ".env")
    db_user = env_vars.get("DATA_DB_USER", "dxdata")
    db_name = env_vars.get("DATA_DB_NAME", "dxdata")
    db_pass = env_vars.get("DATA_DB_PASSWORD", "")
    db_port = env_vars.get("POSTGRES_PORT", "5432")
    db_host = env_vars.get("POSTGRES_HOST", "127.0.0.1")

    # 1. Thử qua docker compose exec nếu container postgres đang chạy
    try:
        ps_proc = subprocess.run(
            ["docker", "compose", "ps", "--status", "running", "-q", "postgres"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            check=False,
        )
        if ps_proc.returncode == 0 and ps_proc.stdout.strip():
            cmd = [
                "docker", "compose", "exec", "-T", "postgres",
                "psql", "-U", db_user, "-d", db_name, "-v", "ON_ERROR_STOP=1", *args
            ]
            proc = subprocess.run(
                cmd,
                cwd=str(REPO_ROOT),
                input=input_data,
                capture_output=True,
                text=True,
                check=False,
            )
            return proc.returncode, proc.stdout, proc.stderr
    except (FileNotFoundError, PermissionError):
        pass

    # 2. Thử qua lệnh psql cục bộ
    try:
        env = os.environ.copy()
        if db_pass:
            env["PGPASSWORD"] = db_pass
        cmd = [
            "psql", "-h", db_host, "-p", db_port, "-U", db_user, "-d", db_name,
            "-v", "ON_ERROR_STOP=1", *args
        ]
        proc = subprocess.run(
            cmd,
            input=input_data,
            capture_output=True,
            text=True,
            env=env,
            check=False,
        )
        return proc.returncode, proc.stdout, proc.stderr
    except (FileNotFoundError, PermissionError):
        pass

    return -1, "", "Không thể kết nối PostgreSQL: không tìm thấy container postgres đang chạy và không có psql trên máy host."


def check_tickets_table() -> bool:
    """Kiểm tra bảng tickets đã tồn tại trong database dxdata chưa."""
    query = "SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'tickets';"
    code, stdout, stderr = run_psql(["-t", "-A", "-c", query])
    if code != 0:
        err = stderr.strip() if stderr else "Không có phản hồi từ máy chủ cơ sở dữ liệu."
        print(f"Cảnh báo kết nối PostgreSQL: {err}", file=sys.stderr)
        return False
    if "1" not in stdout.split():
        print("Chưa có bảng tickets trong PostgreSQL (cần chạy Data API để tạo schema trước). Bỏ qua nạp tickets_seed.sql.", file=sys.stderr)
        return False
    return True


def seed_database() -> bool:
    """Nạp tickets_seed.sql vào PostgreSQL dxdata."""
    sql_file = SAMPLES_DIR / "tickets_seed.sql"
    if not sql_file.exists():
        print(f"Không tìm thấy tệp {sql_file}", file=sys.stderr)
        return False

    if not check_tickets_table():
        return False

    try:
        with open(sql_file, "r", encoding="utf-8") as f:
            sql_content = f.read()
    except OSError as err:
        print(f"Lỗi đọc tệp SQL: {err}", file=sys.stderr)
        return False

    code, stdout, stderr = run_psql([], input_data=sql_content)
    if code != 0:
        print(f"Lỗi khi nạp dữ liệu vào PostgreSQL: {stderr.strip()}", file=sys.stderr)
        return False

    print("Nạp dữ liệu mẫu vào PostgreSQL (dxdata) thành công.")
    return True


def get_quantri_token(env_vars: dict[str, str]) -> str | None:
    """Lấy access token từ Keycloak bằng tài khoản dịch vụ quantri."""
    kc_port = env_vars.get("KEYCLOAK_PORT", "8080")
    kc_realm = env_vars.get("KEYCLOAK_REALM", "dxlab")
    client_id = env_vars.get("KEYCLOAK_CLIENT_ID", "dxlab-app")
    client_secret = env_vars.get("KEYCLOAK_CLIENT_SECRET", "")
    password = env_vars.get("DEMO_USER_PASSWORD", "")

    token_url = f"http://127.0.0.1:{kc_port}/realms/{kc_realm}/protocol/openid-connect/token"
    payload = urllib.parse.urlencode({
        "grant_type": "password",
        "client_id": client_id,
        "client_secret": client_secret,
        "username": "quantri",
        "password": password,
    }).encode("utf-8")

    req = urllib.request.Request(token_url, data=payload, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("access_token")
    except Exception as err:
        print(f"Cảnh báo: không lấy được token quantri từ Keycloak ({err})", file=sys.stderr)
        return None


def seed_seaweedfs(dry_run: bool = False) -> bool:
    """Nạp tệp tài liệu mẫu và metadata sidecar vào SeaweedFS qua API Gateway."""
    guides_file = SAMPLES_DIR / "guides.json"
    if not guides_file.exists():
        print(f"Không tìm thấy tệp {guides_file}", file=sys.stderr)
        return False

    try:
        with open(guides_file, "r", encoding="utf-8") as f:
            guides = json.load(f)
    except (json.JSONDecodeError, OSError) as err:
        print(f"Lỗi đọc tệp {guides_file}: {err}", file=sys.stderr)
        return False

    if dry_run:
        print(f"Đã kiểm tra {len(guides)} tài liệu mẫu trong {guides_file.name}.")
        return True

    env_vars = load_env_file(REPO_ROOT / ".env")
    token = get_quantri_token(env_vars)
    if not token:
        print("Bỏ qua nạp SeaweedFS: Keycloak chưa sẵn sàng hoặc không cấp token cho quantri.", file=sys.stderr)
        return False

    gw_port = env_vars.get("GATEWAY_PORT", "9080")
    gw_host = env_vars.get("GATEWAY_HOST", "127.0.0.1")
    gw_url = f"http://{gw_host}:{gw_port}"

    manifest_paths: list[str] = []

    for guide in guides:
        file_path = guide.get("filePath")
        if not file_path:
            continue
        meta_path = f"{file_path}.meta.json"
        manifest_paths.append(meta_path)

        # 1. Nạp nội dung tài liệu markdown lên SeaweedFS
        content = guide.get("content", "")
        file_url = f"{gw_url}/api/files/{file_path}"
        req = urllib.request.Request(file_url, data=content.encode("utf-8"), method="PUT")
        req.add_header("Authorization", f"Bearer {token}")
        req.add_header("Content-Type", "text/markdown; charset=utf-8")
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                pass
        except urllib.error.HTTPError as err:
            if err.code not in (200, 201, 204):
                print(f"Lỗi nạp tệp {file_path} lên SeaweedFS: {err}", file=sys.stderr)

        # 2. Nạp metadata sidecar JSON (<filePath>.meta.json)
        meta_data = {k: v for k, v in guide.items() if k != "content"}
        meta_url = f"{gw_url}/api/files/{meta_path}"
        meta_body = json.dumps(meta_data, ensure_ascii=False, indent=2).encode("utf-8")
        req_meta = urllib.request.Request(meta_url, data=meta_body, method="PUT")
        req_meta.add_header("Authorization", f"Bearer {token}")
        req_meta.add_header("Content-Type", "application/json; charset=utf-8")
        try:
            with urllib.request.urlopen(req_meta, timeout=10) as resp:
                pass
        except urllib.error.HTTPError as err:
            if err.code not in (200, 201, 204):
                print(f"Lỗi nạp metadata sidecar {meta_path} lên SeaweedFS: {err}", file=sys.stderr)

    # 3. Nạp danh mục manifest portal/manifest.json
    manifest_url = f"{gw_url}/api/files/portal/manifest.json"
    manifest_body = json.dumps(manifest_paths, ensure_ascii=False, indent=2).encode("utf-8")
    req_manifest = urllib.request.Request(manifest_url, data=manifest_body, method="PUT")
    req_manifest.add_header("Authorization", f"Bearer {token}")
    req_manifest.add_header("Content-Type", "application/json; charset=utf-8")
    try:
        with urllib.request.urlopen(req_manifest, timeout=10) as resp:
            pass
    except urllib.error.HTTPError as err:
        if err.code not in (200, 201, 204):
            print(f"Lỗi nạp manifest lên SeaweedFS: {err}", file=sys.stderr)

    print("Nạp tài liệu mẫu và metadata sidecar vào SeaweedFS thành công.")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Nạp dữ liệu mẫu cho DX-Lab")
    parser.add_argument("--dry-run", action="store_true", help="Chỉ kiểm tra tính hợp lệ của tệp dữ liệu mẫu, không ghi vào dịch vụ")
    args = parser.parse_args()

    if not validate_samples():
        sys.exit(1)

    if args.dry_run:
        print("Dữ liệu mẫu hợp lệ.")
        return 0

    db_ok = seed_database()
    fs_ok = seed_seaweedfs()

    print("\n--- Tóm tắt kết quả nạp dữ liệu ---")
    if fs_ok:
        print("ĐÃ NẠP: 6 tài liệu hướng dẫn mẫu và manifest vào SeaweedFS qua tài khoản dịch vụ quantri.")
    else:
        print("BỎ QUA / THẤT BẠI: Nạp tài liệu vào SeaweedFS.")

    if db_ok:
        print("ĐÃ NẠP: Dữ liệu mẫu tickets vào PostgreSQL (dxdata).")
    else:
        print("BỎ QUA: Nạp dữ liệu tickets vào PostgreSQL (cần Data API tạo schema).")

    return 0


if __name__ == "__main__":
    sys.exit(main())


if __name__ == "__main__":
    sys.exit(main())
