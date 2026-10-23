# SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
# SPDX-License-Identifier: Apache-2.0

"""Gateway-facing asset integration with durable status restoration and retries."""

import hmac
import os
import sqlite3
import threading
import time
from contextlib import asynccontextmanager
from pathlib import Path
from uuid import UUID

import jwt
from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from adapter import AssetError, SnipeIT


ROLES = {"ROLE_STUDENT", "ROLE_TECHNICIAN", "ROLE_LAB_MANAGER", "ROLE_ADMIN"}
ISSUER = os.getenv("KEYCLOAK_ISSUER", "http://localhost:8080/realms/dxlab")
JWKS = jwt.PyJWKClient(os.getenv("KEYCLOAK_JWKS_URL", "http://keycloak:8080/realms/dxlab/protocol/openid-connect/certs"),
                       cache_jwk_set=True, lifespan=300)
LOCK = threading.RLock()
STOP = threading.Event()
RETRY_SECONDS = max(10, int(os.getenv("ASSET_RETRY_SECONDS", "60")))


class StatusUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    ticket_id: UUID
    asset_id: int = Field(gt=0)
    to_status: str
    resolution_summary: str | None = None


def caller(authorization: str | None = Header(default=None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Bearer token required")
    try:
        token = authorization[7:]
        key = JWKS.get_signing_key_from_jwt(token).key
        claims = jwt.decode(token, key, algorithms=["RS256"], issuer=ISSUER,
                            options={"verify_aud": False}, leeway=10)
    except (jwt.PyJWTError, jwt.PyJWKClientError, ValueError) as exc:
        raise HTTPException(401, "Invalid access token") from exc
    if claims.get("azp") != os.getenv("KEYCLOAK_CLIENT_ID", "dxlab-app") or claims.get("typ") != "Bearer":
        raise HTTPException(401, "Invalid token client or type")
    if not claims.get("sub") or not claims.get("preferred_username"):
        raise HTTPException(401, "Missing identity claims")
    if not (set(claims.get("realm_access", {}).get("roles", [])) & ROLES):
        raise HTTPException(403, "DX-Helpdesk role required")
    return claims


def internal_key(x_data_api_key: str | None = Header(default=None)):
    expected = os.getenv("DATA_ASSET_KEY", "")
    if not expected or expected == "changeme" or not x_data_api_key or not hmac.compare_digest(x_data_api_key, expected):
        raise HTTPException(403, "Internal service key required")


class Store:
    def __init__(self, path):
        self.path = str(path)
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS asset_updates (
                ticket_id TEXT PRIMARY KEY, asset_id INTEGER NOT NULL,
                original_status_id INTEGER, desired_status TEXT NOT NULL,
                resolution_summary TEXT, result TEXT NOT NULL,
                attempts INTEGER NOT NULL DEFAULT 0, last_error TEXT,
                next_retry_at REAL, updated_at REAL NOT NULL)""")

    def connect(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        return db

    def get(self, ticket_id):
        with self.connect() as db:
            row = db.execute("SELECT * FROM asset_updates WHERE ticket_id=?", (str(ticket_id),)).fetchone()
            return dict(row) if row else None

    def pending(self, update, original):
        with self.connect() as db:
            db.execute("""INSERT INTO asset_updates
                (ticket_id,asset_id,original_status_id,desired_status,resolution_summary,result,next_retry_at,updated_at)
                VALUES (?,?,?,?,?,'PENDING',?,?)
                ON CONFLICT(ticket_id) DO UPDATE SET desired_status=excluded.desired_status,
                    resolution_summary=excluded.resolution_summary, result='PENDING',
                    next_retry_at=excluded.next_retry_at, updated_at=excluded.updated_at""",
                (str(update.ticket_id), update.asset_id, original, update.to_status,
                 update.resolution_summary, time.time() + RETRY_SECONDS, time.time()))

    def set_original(self, ticket_id, status_id):
        with self.connect() as db:
            db.execute("UPDATE asset_updates SET original_status_id=? WHERE ticket_id=? AND original_status_id IS NULL",
                       (status_id, str(ticket_id)))

    def finish(self, ticket_id, success, error=None):
        now = time.time()
        with self.connect() as db:
            db.execute("""UPDATE asset_updates SET result=?, attempts=attempts+1,
                last_error=?, next_retry_at=?, updated_at=? WHERE ticket_id=?""",
                ("SUCCEEDED" if success else "FAILED", error,
                 None if success else now + RETRY_SECONDS, now, str(ticket_id)))

    def due(self):
        with self.connect() as db:
            return [dict(row) for row in db.execute(
                "SELECT * FROM asset_updates WHERE result IN ('FAILED','PENDING') AND next_retry_at<=?",
                (time.time(),)).fetchall()]

    def failures(self):
        with self.connect() as db:
            return [dict(row) for row in db.execute(
                "SELECT * FROM asset_updates WHERE result IN ('FAILED','PENDING') ORDER BY updated_at")]


store = None


def get_store():
    global store
    if store is None:
        store = Store(os.getenv("ASSET_STATE_DB", "/state/updates.sqlite3"))
    return store


def adapter():
    return SnipeIT()


def apply_update(update: StatusUpdate):
    if update.to_status not in ("IN_PROGRESS", "CLOSED"):
        raise HTTPException(422, "Unsupported asset status transition")
    if update.to_status == "CLOSED" and not (update.resolution_summary or "").strip():
        raise HTTPException(422, "Resolution summary required")
    with LOCK:
        db = get_store()
        prior = db.get(update.ticket_id)
        if prior and prior["asset_id"] != update.asset_id:
            raise HTTPException(409, "Ticket asset cannot change during repair")
        if update.to_status == "CLOSED" and not prior:
            raise HTTPException(409, "Original asset status is unknown")
        api = adapter()
        db.pending(update, prior["original_status_id"] if prior else None)
        try:
            asset = api.asset(update.asset_id)
            if not prior or prior["original_status_id"] is None:
                label = asset.get("status_label") or {}
                original = label.get("id") if isinstance(label, dict) else None
                if not isinstance(original, int):
                    raise AssetError("Original asset status is missing")
                db.set_original(update.ticket_id, original)
            else:
                original = prior["original_status_id"]
            if update.to_status == "IN_PROGRESS":
                api.set_status(update.asset_id, api.repair_status_id())
            else:
                note = f"Ticket {update.ticket_id}: {update.resolution_summary.strip()}"
                notes = asset.get("notes") or ""
                if note not in notes:
                    notes = f"{notes}\n{note}".strip()
                api.set_status(update.asset_id, original, notes=notes)
            db.finish(update.ticket_id, True)
            return {"ticket_id": update.ticket_id, "asset_id": update.asset_id,
                    "to_status": update.to_status, "result": "SUCCEEDED"}
        except AssetError as exc:
            db.finish(update.ticket_id, False, str(exc))
            raise HTTPException(503, "Asset update failed; queued for retry") from exc


def retry_failed():
    while not STOP.wait(min(30, RETRY_SECONDS)):
        for row in get_store().due():
            try:
                apply_update(StatusUpdate(ticket_id=row["ticket_id"], asset_id=row["asset_id"],
                                          to_status=row["desired_status"],
                                          resolution_summary=row["resolution_summary"]))
            except HTTPException:
                pass


@asynccontextmanager
async def lifespan(_app):
    get_store()
    STOP.clear()
    worker = threading.Thread(target=retry_failed, daemon=True)
    worker.start()
    yield
    STOP.set()
    worker.join(timeout=2)


app = FastAPI(title="DX-Lab Asset Integration", version="0.1.0",
              root_path="/api/assets", lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/me")
def my_assets(user=Depends(caller)):
    try:
        return adapter().assets_for_username(user["preferred_username"])
    except AssetError as exc:
        raise HTTPException(503, "Asset system unavailable") from exc


@app.get("/bytag/{tag}")
def by_tag(tag: str, _user=Depends(caller)):
    try:
        return adapter().by_tag(tag)
    except AssetError as exc:
        raise HTTPException(503, "Asset system unavailable") from exc


@app.get("/by-id/{asset_id}")
def by_id(asset_id: int, _user=Depends(caller)):
    try:
        return adapter().present(adapter().asset(asset_id))
    except AssetError as exc:
        raise HTTPException(503, "Asset system unavailable") from exc


@app.get("/locations/{location_id}/assets")
def by_location(location_id: int, _user=Depends(caller)):
    try:
        return adapter().by_location(location_id)
    except AssetError as exc:
        raise HTTPException(503, "Asset system unavailable") from exc


@app.post("/internal/status", dependencies=[Depends(caller), Depends(internal_key)])
def update_status(body: StatusUpdate):
    return apply_update(body)


@app.get("/internal/failures", dependencies=[Depends(caller), Depends(internal_key)])
def list_failures():
    return get_store().failures()


@app.post("/internal/retry/{ticket_id}", dependencies=[Depends(caller), Depends(internal_key)])
def retry_ticket(ticket_id: UUID):
    row = get_store().get(ticket_id)
    if not row or row["result"] not in ("FAILED", "PENDING"):
        raise HTTPException(404, "Pending update not found")
    return apply_update(StatusUpdate(ticket_id=ticket_id, asset_id=row["asset_id"],
                                     to_status=row["desired_status"],
                                     resolution_summary=row["resolution_summary"]))
