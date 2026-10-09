#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
# SPDX-License-Identifier: Apache-2.0
#
# Kiểm tra mọi tệp mã/tài liệu được git theo dõi có SPDX-License-Identifier
# trong 10 dòng đầu. Dùng cho CI và `make check-spdx`.

set -euo pipefail

patterns=('*.py' '*.js' '*.ts' '*.vue' '*.sh' '*.yml' '*.yaml' '*.md'
          '*.sql' '*.toml' '*.json5' 'Dockerfile' '*/Dockerfile' 'Makefile'
          '.gitignore' '.env.example')

missing=0
while IFS= read -r f; do
  [ -f "$f" ] || continue
  if ! head -n 10 "$f" | grep -q 'SPDX-License-Identifier:'; then
    echo "Thiếu SPDX header: $f"
    missing=$((missing + 1))
  fi
done < <(git ls-files -- "${patterns[@]}")

if [ "$missing" -gt 0 ]; then
  echo "❌ $missing tệp thiếu SPDX header. Xem CONTRIBUTING.md mục 5."
  exit 1
fi
echo "✅ Mọi tệp đều có SPDX header."
