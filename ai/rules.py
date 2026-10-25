# SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
# SPDX-License-Identifier: Apache-2.0

"""Deterministic suggestions used when the trained model is unavailable."""

import re
import unicodedata


def fold(value: str) -> str:
    value = unicodedata.normalize("NFKD", value.casefold().replace("đ", "d"))
    return " ".join("".join(char for char in value if not unicodedata.combining(char)).split())


CATEGORIES = {
    "HARDWARE": ("máy không lên nguồn", "màn hình", "ổ cứng", "ram", "máy chiếu",
                 "máy in", "nguồn điện", "cháy", "mùi khét", "bàn phím", "chuột"),
    "SOFTWARE_ENVIRONMENT": ("phần mềm", "cài đặt", "windows", "linux", "docker",
                             "ide", "sdk", "bản quyền", "ứng dụng"),
    "NETWORK_ACCOUNT": ("mất mạng", "wifi", "lan", "vlan", "vpn", "mật khẩu",
                        "tài khoản", "đăng nhập", "máy chủ", "đường truyền"),
    "LAB_ASSET": ("mượn máy", "đặt phòng", "bảo trì", "kiểm kê", "tài sản",
                  "đăng ký phòng"),
}
PRIORITIES = {
    "URGENT": ("buổi thi", "phòng thi", "khẩn cấp", "bốc khói", "cháy", "toàn bộ lớp"),
    "HIGH": ("nhiều người", "cả phòng", "máy chủ", "mất mạng", "ngừng hoạt động"),
    "LOW": ("cài thêm", "góp ý", "đề xuất", "ngoài giờ"),
}


def matches(text: str, phrases: tuple[str, ...]) -> list[str]:
    return [phrase for phrase in phrases if re.search(
        rf"(?<!\w){re.escape(fold(phrase))}(?!\w)", text)]


def classify(title: str, description: str) -> dict | None:
    """Return a suggestion only when a category rule has evidence."""
    text = fold(f"{title} {description}")
    found = {category: matches(text, words) for category, words in CATEGORIES.items()}
    category = max(CATEGORIES, key=lambda key: len(found[key]))
    if not found[category]:
        return None
    priority = "MEDIUM"
    priority_words = []
    for level in ("URGENT", "HIGH", "LOW"):
        priority_words = matches(text, PRIORITIES[level])
        if priority_words:
            priority = level
            break
    return {"category": category, "priority": priority,
            "keywords": list(dict.fromkeys(found[category] + priority_words)),
            "source": "rules"}
