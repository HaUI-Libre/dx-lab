# SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
# SPDX-License-Identifier: Apache-2.0

"""Snipe-IT REST adapter; the API layer never handles Snipe-IT response shapes."""

import os
from pathlib import Path
from urllib.parse import quote

import httpx


class AssetError(Exception):
    pass


def _rows(payload):
    if not isinstance(payload, dict) or not isinstance(payload.get("rows"), list):
        raise AssetError("Unexpected Snipe-IT list response")
    return payload["rows"]


def _id(value):
    if isinstance(value, dict):
        return value.get("id")
    return value if isinstance(value, int) else None


def normalize(asset, site=None):
    location = asset.get("location") or asset.get("rtd_location") or {}
    return {"id": asset["id"], "asset_tag": asset["asset_tag"],
            "name": asset.get("name"), "location_id": _id(location),
            "location": location.get("name") if isinstance(location, dict) else None,
            "co_so": site}


class SnipeIT:
    def __init__(self, client=None):
        self.base = os.getenv("SNIPEIT_API_URL", "http://snipeit/api/v1").rstrip("/")
        self.token_file = Path(os.getenv("SNIPEIT_TOKEN_FILE", "/token/snipeit_api_token"))
        self.client = client or httpx.Client(timeout=4)

    def present(self, asset):
        location = asset.get("location") or asset.get("rtd_location")
        location_id = _id(location)
        return normalize(asset, self.site_for_location(location_id) if location_id else None)

    def site_for_location(self, location_id):
        roots = dict(pair.split(":", 1) for pair in
                     os.getenv("ASSET_SITE_ROOTS", "1:CS1,9:CS2,15:CS3").split(","))
        seen = set()
        while location_id and location_id not in seen:
            if str(location_id) in roots:
                return roots[str(location_id)]
            seen.add(location_id)
            location = self.request("GET", f"locations/{location_id}")
            location_id = _id(location.get("parent")) or _id(location.get("parent_id"))
        return None

    def request(self, method, path, **kwargs):
        try:
            token = self.token_file.read_text().strip()
            if not token:
                raise AssetError("Snipe-IT API token is empty")
            response = self.client.request(method, f"{self.base}/{path.lstrip('/')}",
                                           headers={"Authorization": f"Bearer {token}",
                                                    "Accept": "application/json"}, **kwargs)
            response.raise_for_status()
            payload = response.json()
            if isinstance(payload, dict) and payload.get("status") == "error":
                raise AssetError("Snipe-IT rejected the request")
            return payload
        except (OSError, httpx.HTTPError, httpx.InvalidURL, ValueError) as exc:
            raise AssetError("Snipe-IT unavailable or request failed") from exc

    def assets_for_username(self, username):
        users = _rows(self.request("GET", "users", params={"search": username, "limit": 100}))
        match = next((u for u in users if u.get("username") == username), None)
        if not match:
            return []
        return [self.present(a) for a in _rows(self.request(
            "GET", f"users/{match['id']}/assets", params={"limit": 500}))]

    def by_tag(self, tag):
        return self.present(self.request("GET", f"hardware/bytag/{quote(tag, safe='')}"))

    def by_location(self, location_id):
        return [self.present(a) for a in _rows(self.request(
            "GET", f"locations/{location_id}/assets", params={"limit": 500}))]

    def asset(self, asset_id):
        return self.request("GET", f"hardware/{asset_id}")

    def repair_status_id(self):
        label = os.getenv("ASSET_REPAIR_LABEL", "Đang sửa chữa")
        rows = _rows(self.request("GET", "statuslabels", params={"limit": 100}))
        item = next((row for row in rows if row.get("name") == label), None)
        if not item:
            raise AssetError("Repair status label is missing")
        return item["id"]

    def set_status(self, asset_id, status_id, notes=None):
        body = {"status_id": status_id}
        if notes is not None:
            body["notes"] = notes
        payload = self.request("PATCH", f"hardware/{asset_id}", json=body)
        if not isinstance(payload, dict) or payload.get("status") != "success":
            raise AssetError("Snipe-IT did not confirm the asset update")
