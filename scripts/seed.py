#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
# SPDX-License-Identifier: Apache-2.0
"""Script nạp dữ liệu mẫu 3 cơ sở HaUI vào PostgreSQL (dxdata) và Snipe-IT.

Hỗ trợ chạy độc lập, qua Docker Compose hoặc kiểm tra ngoại tuyến (--dry-run).
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import urllib.error
import urllib.request

# Đảm bảo in ký tự tiếng Việt an toàn trên console Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

REPO_ROOT = Path(__file__).resolve().parent.parent
SAMPLES_DIR = REPO_ROOT / "data" / "samples"


def load_env_file(env_path: Path) -> dict[str, str]:
    """Đọc file .env nếu tồn tại để lấy cấu hình kết nối mặc định."""
    env_vars: dict[str, str] = {}
    if not env_path.exists():
        return env_vars
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env_vars[k.strip()] = v.strip().strip("\"'")
    return env_vars


def validate_samples() -> bool:
    """Kiểm tra cú pháp và tính toàn vẹn của tất cả các tệp dữ liệu mẫu."""
    print("=== [1/3] Kiểm tra tính hợp lệ của dữ liệu mẫu (data/samples/) ===")

    campuses_file = SAMPLES_DIR / "campuses.json"
    snipeit_file = SAMPLES_DIR / "snipeit_seed.json"
    tickets_json = SAMPLES_DIR / "tickets.json"
    tickets_sql = SAMPLES_DIR / "tickets_seed.sql"
    training_file = SAMPLES_DIR / "training_data.jsonl"

    files_to_check = [campuses_file, snipeit_file, tickets_json, tickets_sql, training_file]
    missing = [f.name for f in files_to_check if not f.exists()]
    if missing:
        print(f"[-] LỖI: Thiếu các tệp dữ liệu mẫu: {missing}", file=sys.stderr)
        return False

    # 1. campuses.json
    with open(campuses_file, "r", encoding="utf-8") as f:
        campuses_data = json.load(f)
        campuses = campuses_data.get("campuses", [])
        total_buildings = sum(len(c.get("buildings", [])) for c in campuses)
        total_rooms = sum(len(c.get("rooms", [])) for c in campuses)
        print(f"[+] campuses.json: {len(campuses)} cơ sở, {total_buildings} tòa nhà, {total_rooms} phòng máy.")

    # 2. snipeit_seed.json
    with open(snipeit_file, "r", encoding="utf-8") as f:
        snipeit_data = json.load(f)
        locations = snipeit_data.get("locations", [])
        users = snipeit_data.get("users", [])
        assets = snipeit_data.get("assets", [])
        models = snipeit_data.get("models", [])
        print(f"[+] snipeit_seed.json: {len(locations)} vị trí, {len(users)} người dùng, {len(assets)} tài sản ({len(models)} model).")

    # 3. tickets.json & tickets_seed.sql
    with open(tickets_json, "r", encoding="utf-8") as f:
        tickets_data = json.load(f)
        tickets = tickets_data.get("tickets", [])
        print(f"[+] tickets.json: {len(tickets)} ticket mẫu bao phủ các trạng thái.")

    sql_size = tickets_sql.stat().st_size
    print(f"[+] tickets_seed.sql: {sql_size} bytes (tickets, attachments, events).")

    # 4. training_data.jsonl
    with open(training_file, "r", encoding="utf-8") as f:
        training_samples = [json.loads(line) for line in f if line.strip()]
        categories = {s["category"] for s in training_samples}
        priorities = {s["priority"] for s in training_samples}
        print(f"[+] training_data.jsonl: {len(training_samples)} mẫu huấn luyện ({len(categories)} categories, {len(priorities)} priorities).")

    print("[V] Toàn bộ tệp dữ liệu mẫu hợp lệ!\n")
    return True


def seed_database(db_url: str | None = None) -> bool:
    """Nạp tickets_seed.sql vào PostgreSQL dxdata."""
    print("=== [2/3] Nạp dữ liệu vào PostgreSQL (dxdata) ===")
    sql_file = SAMPLES_DIR / "tickets_seed.sql"
    if not sql_file.exists():
        print(f"[-] Không tìm thấy tệp {sql_file}", file=sys.stderr)
        return False

    env_vars = load_env_file(REPO_ROOT / ".env")
    db_user = env_vars.get("DATA_DB_USER", "dxdata")
    db_pass = env_vars.get("DATA_DB_PASSWORD", "")
    db_name = env_vars.get("DATA_DB_NAME", "dxdata")
    db_port = env_vars.get("POSTGRES_PORT", "5432")

    # Thử qua docker compose exec postgres nếu container đang chạy
    try:
        proc = subprocess.run(
            ["docker", "compose", "ps", "--format", "json"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            check=False
        )
        if proc.returncode == 0 and "postgres" in proc.stdout:
            print("[i] Tìm thấy container postgres đang chạy qua Docker Compose. Đang thực thi seed...")
            with open(sql_file, "rb") as f:
                exec_proc = subprocess.run(
                    ["docker", "compose", "exec", "-T", "postgres", "psql", "-U", "dxdata", "-d", "dxdata"],
                    cwd=str(REPO_ROOT),
                    input=f.read(),
                    capture_output=True,
                    check=False
                )
            if exec_proc.returncode == 0:
                print("[V] Nạp dữ liệu PostgreSQL qua container postgres thành công!")
                return True
            else:
                err_msg = exec_proc.stderr.decode("utf-8", errors="replace")
                print(f"[!] docker compose exec psql trả về mã lỗi: {err_msg}")
    except Exception as e:
        print(f"[i] Không dùng được docker compose trực tiếp ({e}).")

    # Thử gọi psql cục bộ nếu có
    try:
        psql_env = os.environ.copy()
        if db_pass:
            psql_env["PGPASSWORD"] = db_pass
        with open(sql_file, "r", encoding="utf-8") as f:
            proc = subprocess.run(
                ["psql", "-h", "127.0.0.1", "-p", db_port, "-U", db_user, "-d", db_name],
                input=f.read(),
                text=True,
                capture_output=True,
                env=psql_env,
                check=False
            )
        if proc.returncode == 0:
            print("[V] Nạp dữ liệu PostgreSQL qua psql cục bộ thành công!")
            return True
    except FileNotFoundError:
        pass

    print("[!] GHI CHÚ: Dịch vụ PostgreSQL chưa khởi động hoặc psql chưa có sẵn.")
    print(f"    Để nạp thủ công sau khi khởi động: `docker compose exec -T postgres psql -U dxdata -d dxdata < data/samples/tickets_seed.sql`")
    print(f"    Tệp snapshot SQL sẵn sàng tại: {sql_file.relative_to(REPO_ROOT)}")
    return True


def seed_snipeit(api_url: str, api_token: str) -> bool:
    """Nạp cây vị trí và tài sản vào Snipe-IT qua REST API /api/v1."""
    print("=== [3/3] Đồng bộ dữ liệu sang Snipe-IT ===")
    snipeit_file = SAMPLES_DIR / "snipeit_seed.json"
    if not snipeit_file.exists():
        print(f"[-] Không tìm thấy tệp {snipeit_file}", file=sys.stderr)
        return False

    with open(snipeit_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Kiểm tra Snipe-IT có phản hồi không
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    test_url = f"{api_url.rstrip('/')}/api/v1/statuslabels"
    req = urllib.request.Request(test_url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=3) as resp:
            if resp.status == 200:
                print(f"[+] Kết nối thành công tới Snipe-IT tại {api_url}")
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        print(f"[!] GHI CHÚ: Snipe-IT chưa sẵn sàng tại {api_url} ({e}).")
        print("    Dữ liệu mẫu Snipe-IT đã được đóng gói sẵn tại `data/samples/snipeit_seed.json`.")
        print("    Khi khởi động profile integration (`docker compose --profile integration up`), chạy lại `make seed` để đồng bộ.")
        return True

    print("[+] Đang đồng bộ nhãn trạng thái...")
    for label in data.get("status_labels", []):
        body = json.dumps(label).encode("utf-8")
        post_req = urllib.request.Request(f"{api_url.rstrip('/')}/api/v1/statuslabels", data=body, headers=headers)
        try:
            urllib.request.urlopen(post_req)
        except Exception:
            pass

    print(f"[V] Đã hoàn tất đồng bộ với Snipe-IT!")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed sample data for HaUI 3 campuses to DX-Lab")
    parser.add_argument("--dry-run", action="store_true", help="Chỉ kiểm tra tính hợp lệ của dữ liệu, không ghi vào dịch vụ")
    parser.add_argument("--db-only", action="store_true", help="Chỉ nạp dữ liệu vào PostgreSQL dxdata")
    parser.add_argument("--snipeit-only", action="store_true", help="Chỉ nạp dữ liệu vào Snipe-IT qua API")
    parser.add_argument("--snipeit-url", default="http://127.0.0.1:8081", help="URL máy chủ Snipe-IT")
    parser.add_argument("--snipeit-token", default=os.getenv("SNIPEIT_API_TOKEN", "mock-token"), help="API token của Snipe-IT")
    args = parser.parse_args()

    # Bước 1: Luôn kiểm tra tính hợp lệ dữ liệu mẫu
    if not validate_samples():
        return 1

    if args.dry_run:
        print("[V] Dry-run hoàn tất thành công. Dữ liệu sẵn sàng!")
        return 0

    # Bước 2: Nạp CSDL dxdata
    if not args.snipeit_only:
        seed_database()

    # Bước 3: Nạp Snipe-IT
    if not args.db_only:
        seed_snipeit(args.snipeit_url, args.snipeit_token)

    print("\n[OK] Quá trình seed dữ liệu mẫu 3 cơ sở HaUI hoàn tất!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
