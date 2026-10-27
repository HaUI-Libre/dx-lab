# SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
# SPDX-License-Identifier: Apache-2.0

"""DX-Helpdesk Data API. Flowable owns tasks; this service owns ticket data."""

import asyncio
import json
import logging
import os
import threading
import time
from contextlib import asynccontextmanager, contextmanager
from datetime import datetime
from enum import Enum
from uuid import UUID

import httpx
import jwt
import nats
import pg8000.dbapi
from nats.js.errors import NotFoundError
from prometheus_client import CollectorRegistry, Counter, Histogram, start_http_server
from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request, Response
from fastapi.responses import StreamingResponse
from starlette.concurrency import run_in_threadpool
from pydantic import BaseModel, ConfigDict, Field


METRICS = CollectorRegistry()
REQUESTS = Histogram("dxlab_data_request_seconds", "Data API request duration",
                     ["method", "route", "status"], registry=METRICS)
TRANSITIONS = Counter("dxlab_ticket_transitions_total", "Ticket workflow actions completed",
                      ["action", "to_status", "co_so"], registry=METRICS)
ASSET_UPDATES = Counter("dxlab_asset_status_updates_total",
                        "Asset status update hand-offs by outcome", ["outcome"], registry=METRICS)


@asynccontextmanager
async def lifespan(_app):
    # Metrics on their own port: the gateway routes /api/data to 8000 only
    start_http_server(int(os.getenv("METRICS_PORT", "9100")), registry=METRICS)
    yield


app = FastAPI(title="DX-Lab Data API", version="0.3.0", root_path="/api/data", lifespan=lifespan)


@app.middleware("http")
async def observe(request: Request, call_next):
    started = time.perf_counter()
    response = await call_next(request)
    route = request.scope.get("route")
    REQUESTS.labels(request.method, getattr(route, "path", "unmatched"),
                    str(response.status_code)).observe(time.perf_counter() - started)
    return response
ROLES = {"ROLE_STUDENT", "ROLE_TECHNICIAN", "ROLE_LAB_MANAGER", "ROLE_ADMIN"}
ISSUER = os.getenv("KEYCLOAK_ISSUER", "http://localhost:8080/realms/dxlab")
JWKS_URL = os.getenv("KEYCLOAK_JWKS_URL", "http://keycloak:8080/realms/dxlab/protocol/openid-connect/certs")
JWKS = jwt.PyJWKClient(JWKS_URL, cache_jwk_set=True, lifespan=300)
FLOWABLE_URL = os.getenv("DATA_WORKFLOW_URL", "http://apisix:9080/api/workflow/data")
NATS_URL = os.getenv("NATS_URL", "").strip()
STATUS_SUBJECT = "dxlab.ticket.status_changed"
STATUS_STREAM = "DXLAB_TICKETS"
# After a failed publish, skip the bus for a while so requests do not each wait on it
BUS_RETRY_AFTER = 30
# SSE: a comment line this often keeps the gateway's 60 s read timeout from closing the stream
STREAM_HEARTBEAT = 15
STREAM_FIELDS = ("ticket_id", "action", "from_status", "to_status", "co_so", "actor_sub", "occurred_at")
_bus_down_until = 0.0
log = logging.getLogger("dxlab.data")
ASSET_URL = os.getenv("DATA_ASSET_URL", "http://apisix:9080/api/assets")


def asset_location(asset_id: int, token: str) -> int | None:
    try:
        response = httpx.get(f"{ASSET_URL}/by-id/{asset_id}",
                             headers={"Authorization": f"Bearer {token}"}, timeout=5)
        if response.status_code == 404:
            raise HTTPException(422, "Unknown asset")
        response.raise_for_status()
        location_id = response.json().get("location_id")
        if not isinstance(location_id, int) or location_id <= 0:
            return None
        return location_id
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(503, "Asset system unavailable") from exc


class Category(str, Enum):
    HARDWARE = "HARDWARE"
    SOFTWARE_ENVIRONMENT = "SOFTWARE_ENVIRONMENT"
    NETWORK_ACCOUNT = "NETWORK_ACCOUNT"
    LAB_ASSET = "LAB_ASSET"


class Priority(str, Enum):
    URGENT = "URGENT"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class Status(str, Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"
    REJECTED = "REJECTED"


class Source(str, Enum):
    DX_HELPDESK = "dx-helpdesk"
    SNIPE_IT = "snipe-it"
    NATS = "nats"


class Draft(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1)
    category: Category | None = None
    priority: Priority | None = None
    location: str | None = None
    location_id: int | None = Field(default=None, gt=0)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    asset_id: int | None = Field(default=None, gt=0)


class DraftPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, min_length=1)
    category: Category | None = None
    priority: Priority | None = None
    location: str | None = None
    location_id: int | None = Field(default=None, gt=0)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    asset_id: int | None = Field(default=None, gt=0)


class Action(str, Enum):
    submit = "submit"
    accept = "accept"
    reject = "reject"
    assign = "assign"
    start = "start"
    resolve = "resolve"
    close = "close"
    reopen = "reopen"


class ActionBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reason: str | None = None
    technician_sub: str | None = None
    resolution_summary: str | None = None
    priority: Priority | None = None


class AttachmentBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    # Key the app chose when uploading through /api/files: tickets/<ticket_id>/<file>
    storage_key: str = Field(pattern=r"^tickets/[0-9a-f-]{36}/[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
    file_name: str = Field(min_length=1, max_length=255)
    content_type: str = Field(pattern=r"^(image/(png|jpeg|webp)|application/pdf)$")
    size_bytes: int = Field(ge=1, le=20 * 1024 * 1024)


class RatingBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    rating: int = Field(ge=1, le=5)


def caller(authorization: str | None = Header(default=None)) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Bearer token required")
    token = authorization[7:]
    try:
        key = JWKS.get_signing_key_from_jwt(token).key
        claims = jwt.decode(token, key, algorithms=["RS256"], issuer=ISSUER,
                            options={"verify_aud": False},
                            leeway=10)
    except (jwt.PyJWTError, jwt.PyJWKClientError, ValueError) as exc:
        raise HTTPException(401, "Invalid access token") from exc
    if claims.get("azp") != os.getenv("KEYCLOAK_CLIENT_ID", "dxlab-app"):
        raise HTTPException(401, "Invalid token client")
    if claims.get("typ") != "Bearer":
        raise HTTPException(401, "Access token required")
    if not claims.get("sub") or not claims.get("preferred_username"):
        raise HTTPException(401, "Missing identity claims")
    roles = set(claims.get("realm_access", {}).get("roles", [])) & ROLES
    if not roles:
        raise HTTPException(403, "DX-Helpdesk role required")
    return {"sub": claims["sub"], "username": claims["preferred_username"],
            "co_so": claims.get("co_so"), "roles": roles, "token": token}


@contextmanager
def database():
    db = pg8000.dbapi.connect(
        host=os.getenv("DATA_DB_HOST", "postgres"), port=5432,
        database="dxdata", user="dxdata", password=os.environ["DATA_DB_PASSWORD"])
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def one(db, sql, params=()):
    cur = db.cursor()
    cur.execute(sql, params)
    row = cur.fetchone()
    return dict(zip((col[0] for col in cur.description), row)) if row else None


def location_point(db, location_id: int) -> tuple[float, float]:
    row = one(db, "SELECT ST_X(point) AS longitude, ST_Y(point) AS latitude "
              "FROM location_points WHERE location_id = %s", (location_id,))
    if not row:
        raise HTTPException(422, "Unknown asset location")
    return row["longitude"], row["latitude"]


def spatial_site(db, longitude: float, latitude: float) -> str:
    site = one(db, """WITH p AS (SELECT ST_SetSRID(ST_MakePoint(%s,%s),4326) AS geom)
        SELECT code AS co_so FROM campus_areas, p
        ORDER BY CASE WHEN ST_Contains(boundary,p.geom) THEN 0 ELSE 1 END,
                 ST_Distance(boundary::geography,p.geom::geography), code LIMIT 1""",
               (longitude, latitude))
    if not site:
        raise HTTPException(503, "Campus boundaries unavailable")
    return site["co_so"]


def many(db, sql, params=()):
    cur = db.cursor()
    cur.execute(sql, params)
    names = [col[0] for col in cur.description]
    return [dict(zip(names, row)) for row in cur.fetchall()]


def execute(db, sql, params=()):
    cur = db.cursor()
    cur.execute(sql, params)


def visible(ticket, user):
    if "ROLE_ADMIN" in user["roles"]:
        return True
    if "ROLE_LAB_MANAGER" in user["roles"]:
        return bool((user["co_so"] and ticket["co_so"] == user["co_so"]) or
                    (ticket["status"] == "DRAFT" and ticket["created_by"] == user["sub"]))
    if "ROLE_TECHNICIAN" in user["roles"]:
        return bool(ticket["created_by"] == user["sub"] or
                    (user["co_so"] and ticket["co_so"] == user["co_so"]
                     and ticket["assigned_to"] == user["sub"]))
    return ticket["created_by"] == user["sub"]


def ticket_for(db, ticket_id, user, lock=False):
    row = one(db, "SELECT * FROM tickets WHERE id = %s AND deleted_at IS NULL" +
              (" FOR UPDATE" if lock else ""), (ticket_id,))
    if not row or not visible(row, user):
        raise HTTPException(404, "Ticket not found")
    return row


def event(db, ticket_id, action, user, before, after, details=None,
          source: Source = Source.DX_HELPDESK):
    execute(db, """INSERT INTO ticket_events
        (ticket_id, action, actor_sub, source, from_status, to_status, details)
        VALUES (%s,%s,%s,%s,%s,%s,%s::jsonb)""",
        (ticket_id, action, user["sub"], Source(source).value, before, after,
         json.dumps(details or {}, default=str)))


def record_asset_status_update(user, ticket):
    """Best-effort M2 integration; persist outcome without changing workflow state."""
    url = os.getenv("DATA_ASSET_STATUS_URL", "").strip()
    key = os.getenv("DATA_ASSET_KEY", "")
    outcome = "FAILED"
    reason = None
    http_status = None
    if not ticket["asset_id"]:
        reason = "missing_asset_id"
    elif not url:
        reason = "integration_not_configured"
    elif not key or key == "changeme":
        reason = "integration_key_not_configured"
    else:
        payload = {"ticket_id": str(ticket["id"]), "asset_id": ticket["asset_id"],
                   "to_status": ticket["status"]}
        if ticket["status"] == "CLOSED":
            payload["resolution_summary"] = ticket["resolution_summary"]
        try:
            response = httpx.post(url, json=payload,
                                  headers={"Authorization": f"Bearer {user['token']}",
                                           "X-Data-Api-Key": key},
                                  timeout=15)
            http_status = response.status_code
            response.raise_for_status()
            outcome = "SUCCEEDED"
        except (httpx.HTTPError, httpx.InvalidURL) as exc:
            reason = "http_error" if isinstance(exc, httpx.HTTPStatusError) else "transport_error"
    details = {"asset_id": ticket["asset_id"], "target_status": ticket["status"],
               "outcome": outcome, "target_source": Source.SNIPE_IT.value}
    if reason:
        details["reason"] = reason
    if http_status is not None:
        details["http_status"] = http_status
    ASSET_UPDATES.labels(outcome).inc()
    with database() as db:
        event(db, ticket["id"], f"ASSET_STATUS_UPDATE_{outcome}", user,
              ticket["status"], ticket["status"], details,
              source=Source.SNIPE_IT if outcome == "SUCCEEDED" else Source.DX_HELPDESK)


async def _publish(payload, msg_id):
    nc = await nats.connect(NATS_URL, connect_timeout=2, allow_reconnect=False,
                            max_reconnect_attempts=0)
    try:
        js = nc.jetstream()
        try:
            await js.stream_info(STATUS_STREAM)
        except NotFoundError:
            await js.add_stream(name=STATUS_STREAM, subjects=["dxlab.ticket.>"])
        # Nats-Msg-Id lets JetStream drop a duplicate if the same change is sent twice
        await js.publish(STATUS_SUBJECT, json.dumps(payload, default=str).encode(),
                         headers={"Nats-Msg-Id": msg_id}, timeout=3)
    finally:
        await nc.close()


def publish_status_changed(user, before, ticket, action):
    """Publish after the PostgreSQL commit; False means the bus is not available."""
    global _bus_down_until
    if not NATS_URL or time.monotonic() < _bus_down_until:
        return False
    payload = {"ticket_id": str(ticket["id"]), "action": action, "from_status": before,
               "to_status": ticket["status"], "asset_id": ticket["asset_id"],
               "co_so": ticket["co_so"], "resolution_summary": ticket["resolution_summary"],
               "actor_sub": user["sub"], "occurred_at": ticket["updated_at"]}
    msg_id = f"{ticket['id']}:{ticket['status']}:{ticket['updated_at']}"
    outcome = {}

    def send():
        try:
            asyncio.run(_publish(payload, msg_id))
            outcome["ok"] = True
        except Exception as exc:
            outcome["error"] = exc

    # Own thread with a bounded join: resolving an absent nats host can block far longer
    # than any request should wait, and asyncio.run would wait for that lookup to end.
    worker = threading.Thread(target=send, daemon=True)
    worker.start()
    worker.join(timeout=3)
    if outcome.get("ok"):
        return True
    _bus_down_until = time.monotonic() + BUS_RETRY_AFTER
    log.warning("Cannot publish %s for ticket %s: %r", STATUS_SUBJECT, ticket["id"],
                outcome.get("error", "timeout"))
    return False


def record_asset_update_queued(user, ticket):
    ASSET_UPDATES.labels("QUEUED").inc()
    with database() as db:
        event(db, ticket["id"], "ASSET_STATUS_UPDATE_QUEUED", user, ticket["status"], ticket["status"],
              {"asset_id": ticket["asset_id"], "target_status": ticket["status"],
               "target_source": Source.SNIPE_IT.value, "subject": STATUS_SUBJECT},
              source=Source.NATS)


def flowable(user, method, path, payload=None, params=None):
    key = os.getenv("DATA_WORKFLOW_KEY")
    if not key or key == "changeme":
        raise HTTPException(503, "Workflow service key not configured")
    try:
        response = httpx.request(method, f"{FLOWABLE_URL}/{path}",
                                 headers={"Authorization": f"Bearer {user['token']}",
                                          "X-Data-Api-Key": key},
                                 json=payload, params=params, timeout=10)
        response.raise_for_status()
        return response.json() if response.content else None
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(503, "Workflow unavailable or out of sync") from exc


def variables(**values):
    return [{"name": name, "value": value} for name, value in values.items()]


def current_task(user, ticket, expected):
    result = flowable(user, "GET", "runtime/tasks",
                      params={"processInstanceId": ticket["workflow_instance_id"]})
    tasks = result.get("data", [])
    if len(tasks) != 1 or tasks[0].get("taskDefinitionKey") != expected:
        raise HTTPException(409, "Workflow task does not match ticket status")
    return tasks[0]


def keycloak_admin():
    """Return the realm admin base URL and auth headers for server-side lookups.

    Uses the dxlab-data-api service account, which only holds realm-management
    view-users, so a leaked Data API secret cannot change users or roles.
    """
    base = os.getenv("KEYCLOAK_INTERNAL_URL", "http://keycloak:8080")
    realm = os.getenv("KEYCLOAK_REALM", "dxlab")
    token_response = httpx.post(f"{base}/realms/{realm}/protocol/openid-connect/token",
                                data={"grant_type": "client_credentials",
                                      "client_id": os.getenv("DATA_API_CLIENT_ID", "dxlab-data-api"),
                                      "client_secret": os.environ["DATA_API_CLIENT_SECRET"]},
                                timeout=10)
    token_response.raise_for_status()
    return (f"{base}/admin/realms/{realm}",
            {"Authorization": f"Bearer {token_response.json()['access_token']}"})


def technician(sub, site):
    """Resolve a Keycloak subject server-side; never trust a UI supplied site."""
    try:
        sub = str(UUID(sub))
    except ValueError as exc:
        raise HTTPException(422, "Invalid technician_sub") from exc
    try:
        admin, headers = keycloak_admin()
        user_response = httpx.get(f"{admin}/users/{sub}",
                                  headers=headers, timeout=10)
        user_response.raise_for_status()
        roles_response = httpx.get(f"{admin}/users/{sub}/role-mappings/realm/composite",
                                   headers=headers, timeout=10)
        roles_response.raise_for_status()
        record = user_response.json()
        roles = {r["name"] for r in roles_response.json()}
    except (httpx.HTTPError, KeyError, ValueError) as exc:
        raise HTTPException(503, "Cannot verify technician") from exc
    if not record.get("enabled") or record.get("attributes", {}).get("co_so") != [site] \
            or "ROLE_TECHNICIAN" not in roles:
        raise HTTPException(422, "Technician must belong to ticket site")
    return record["username"]


@app.get("/health")
def health():
    return {"status": "ok"}


def stream_payload(raw, user, lookup):
    """One NATS status_changed message as the SSE data the caller may see, or None.

    The bus carries every ticket; visibility is decided per message from the current row,
    with the same rule as GET /tickets/{id}, so nobody learns about tickets they cannot open.
    """
    try:
        payload = json.loads(raw)
        ticket_id = str(UUID(str(payload["ticket_id"])))
    except (ValueError, KeyError, TypeError):
        return None
    ticket = lookup(ticket_id)
    if not ticket or not visible(ticket, user):
        return None
    out = {key: payload.get(key) for key in STREAM_FIELDS}
    out["ticket_id"] = ticket_id
    out["title"] = ticket["title"]
    return out


def stream_ticket(ticket_id):
    with database() as db:
        return one(db, "SELECT id, title, status, co_so, created_by, assigned_to FROM tickets "
                       "WHERE id = %s AND deleted_at IS NULL", (ticket_id,))


def token_expiry(token):
    try:
        return float(jwt.decode(token, options={"verify_signature": False}).get("exp") or 0)
    except jwt.PyJWTError:
        return 0.0


@app.get("/events/stream")
async def stream_ticket_events(request: Request, user=Depends(caller)):
    """Server-Sent Events: status changes of tickets the caller may see, read from NATS.

    A plain subscription is enough here: a missed event while disconnected only means the
    page reloads its data on reconnect, unlike asset-sync which needs a durable consumer.
    """
    if not NATS_URL:
        raise HTTPException(503, "Event bus not configured")
    try:
        # wait_for bounds DNS lookup of an absent nats host as well as the TCP connect
        nc = await asyncio.wait_for(nats.connect(NATS_URL, connect_timeout=2, allow_reconnect=False,
                                                 max_reconnect_attempts=0), timeout=3)
    except Exception as exc:
        raise HTTPException(503, "Event bus unavailable") from exc
    queue: asyncio.Queue = asyncio.Queue(maxsize=200)

    async def on_message(msg):
        if not queue.full():
            queue.put_nowait(msg.data)

    sub = await nc.subscribe(STATUS_SUBJECT, cb=on_message)
    expires = token_expiry(user["token"])

    async def frames():
        try:
            yield "retry: 5000\n: connected\n\n"
            while True:
                if await request.is_disconnected():
                    return
                # The token was checked once; end the stream when it expires so the client
                # reconnects with a fresh one instead of listening on stale permissions.
                if expires and time.time() >= expires:
                    yield "event: expired\ndata: {}\n\n"
                    return
                if not nc.is_connected:
                    yield "event: bus-down\ndata: {}\n\n"
                    return
                try:
                    raw = await asyncio.wait_for(queue.get(), STREAM_HEARTBEAT)
                except asyncio.TimeoutError:
                    yield ": ping\n\n"
                    continue
                data = await run_in_threadpool(stream_payload, raw, user, stream_ticket)
                if data:
                    yield f"event: status\ndata: {json.dumps(data, default=str)}\n\n"
        finally:
            try:
                await sub.unsubscribe()
                await nc.close()
            except Exception:
                pass

    return StreamingResponse(frames(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.get("/locations")
def list_locations(user=Depends(caller)):
    """Locations the reporter can pick when the asset system is unavailable."""
    with database() as db:
        return many(db, "SELECT location_id, code, co_so FROM site_locations ORDER BY location_id")


@app.get("/technicians")
def list_technicians(co_so: str | None = Query(None, pattern="^CS[1-3]$"), user=Depends(caller)):
    """Technicians a manager may assign: only those of the manager's own site."""
    if "ROLE_ADMIN" in user["roles"]:
        site = co_so
        if not site:
            raise HTTPException(422, "co_so required for admin")
    elif "ROLE_LAB_MANAGER" in user["roles"] and user["co_so"]:
        site = user["co_so"]
    else:
        raise HTTPException(403, "Manager of a site required")
    # Search by attribute, then check roles per user: both need only view-users, while
    # listing a role's members would also need view-realm.
    try:
        admin, headers = keycloak_admin()
        response = httpx.get(f"{admin}/users",
                             params={"q": f"co_so:{site}", "briefRepresentation": "false", "max": 500},
                             headers=headers, timeout=10)
        response.raise_for_status()
        result = []
        for u in response.json():
            if not u.get("enabled") or u.get("attributes", {}).get("co_so") != [site]:
                continue
            roles = httpx.get(f"{admin}/users/{u['id']}/role-mappings/realm/composite",
                              headers=headers, timeout=10)
            roles.raise_for_status()
            if "ROLE_TECHNICIAN" in {r["name"] for r in roles.json()}:
                result.append({"sub": u["id"], "username": u["username"],
                               "name": " ".join(p for p in (u.get("firstName"), u.get("lastName")) if p)
                               or u["username"], "co_so": site})
    except (httpx.HTTPError, KeyError, ValueError) as exc:
        raise HTTPException(503, "Cannot list technicians") from exc
    return result


@app.post("/tickets", status_code=201)
def create_ticket(body: Draft, response: Response, user=Depends(caller)):
    if not body.title.strip() or not body.description.strip():
        raise HTTPException(422, "Title and description cannot be blank")
    with database() as db:
        row = one(db, """INSERT INTO tickets
            (title, description, category, priority, location, location_id,
             latitude, longitude, asset_id, created_by)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING *""",
            (body.title.strip(), body.description.strip(), body.category, body.priority,
             body.location, body.location_id, body.latitude, body.longitude,
             body.asset_id, user["sub"]))
        event(db, row["id"], "CREATE_DRAFT", user, None, "DRAFT",
              {"title": row["title"], "category": row["category"],
               "priority": row["priority"], "asset_id": row["asset_id"],
               "location_id": row["location_id"], "latitude": row["latitude"],
               "longitude": row["longitude"]})
    response.headers["Location"] = f"/api/data/tickets/{row['id']}"
    return row


@app.get("/tickets")
def list_tickets(status: Status | None = None, category: Category | None = None,
                 priority: Priority | None = None, q: str | None = Query(None, min_length=1),
                 page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
                 user=Depends(caller)):
    clauses = ["deleted_at IS NULL"]
    params = []
    if "ROLE_ADMIN" not in user["roles"]:
        if "ROLE_LAB_MANAGER" in user["roles"]:
            clauses.append("((status = 'DRAFT' AND created_by = %s) OR co_so = %s)")
            params += [user["sub"], user["co_so"]]
        elif "ROLE_TECHNICIAN" in user["roles"]:
            clauses.append("(created_by = %s OR (assigned_to = %s AND co_so = %s))")
            params += [user["sub"], user["sub"], user["co_so"]]
        else:
            clauses.append("created_by = %s")
            params.append(user["sub"])
    for field, value in (("status", status), ("category", category), ("priority", priority)):
        if value:
            clauses.append(f"{field} = %s")
            params.append(value.value)
    if q:
        clauses.append("(title ILIKE %s OR description ILIKE %s OR code ILIKE %s)")
        params += [f"%{q}%"] * 3
    where = " AND ".join(clauses)
    with database() as db:
        total = one(db, f"SELECT count(*) AS count FROM tickets WHERE {where}", params)["count"]
        items = many(db, f"SELECT * FROM tickets WHERE {where} ORDER BY created_at DESC, id DESC "
                     "LIMIT %s OFFSET %s", params + [page_size, (page - 1) * page_size])
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@app.get("/stats")
def ticket_stats(co_so: str | None = Query(None, pattern="^CS[1-3]$"),
                 from_: datetime | None = Query(None, alias="from"),
                 to: datetime | None = None, user=Depends(caller)):
    """Dashboard counts (#22). Managers get their own site from the token; admins all
    sites or the one in co_so. Unsent drafts and deleted tickets are not counted."""
    if "ROLE_ADMIN" in user["roles"]:
        site = co_so
    elif "ROLE_LAB_MANAGER" in user["roles"] and user["co_so"]:
        if co_so and co_so != user["co_so"]:
            raise HTTPException(403, "Managers see only their own site")
        site = user["co_so"]
    else:
        raise HTTPException(403, "Manager of a site or admin required")
    if from_ and to and from_ >= to:
        raise HTTPException(422, "from must be earlier than to")
    clauses = ["t.deleted_at IS NULL", "t.status <> 'DRAFT'"]
    params = []
    for clause, value in (("t.co_so = %s", site), ("t.created_at >= %s", from_),
                          ("t.created_at < %s", to)):
        if value:
            clauses.append(clause)
            params.append(value)
    where = " AND ".join(clauses)

    def counts(db, field):
        rows = many(db, f"SELECT t.{field} AS key, count(*) AS n FROM tickets t "
                    f"WHERE {where} GROUP BY t.{field}", params)
        return {row["key"]: row["n"] for row in rows if row["key"]}

    with database() as db:
        by_status = counts(db, "status")
        summary = one(db, f"""SELECT
            avg(extract(epoch FROM t.resolved_at - t.submitted_at)) / 3600 AS hours,
            count(*) FILTER (WHERE t.sla_due_at < now()
                             AND t.status NOT IN ('CLOSED', 'REJECTED')) AS overdue
            FROM tickets t WHERE {where}""", params)
        reopens = one(db, f"""SELECT count(*) AS n FROM ticket_events e
            JOIN tickets t ON t.id = e.ticket_id
            WHERE e.action = 'REOPEN' AND {where}""", params)
        result = {"total": sum(by_status.values()), "by_status": by_status,
                  "by_category": counts(db, "category"), "by_co_so": counts(db, "co_so"),
                  "average_resolution_hours": None if summary["hours"] is None
                  else round(float(summary["hours"]), 2),
                  "overdue_count": summary["overdue"], "reopen_count": reopens["n"]}
    return result


@app.get("/tickets/{ticket_id}")
def get_ticket(ticket_id: UUID, user=Depends(caller)):
    with database() as db:
        return ticket_for(db, ticket_id, user)


@app.get("/tickets/{ticket_id}/events")
def list_ticket_events(ticket_id: UUID, user=Depends(caller)):
    with database() as db:
        ticket_for(db, ticket_id, user)
        return many(db, """SELECT * FROM ticket_events WHERE ticket_id = %s
            ORDER BY occurred_at, id""", (ticket_id,))


@app.get("/tickets/{ticket_id}/attachments")
def list_attachments(ticket_id: UUID, user=Depends(caller)):
    with database() as db:
        ticket_for(db, ticket_id, user)
        return many(db, """SELECT id, ticket_id, storage_key, file_name, content_type, size_bytes,
            source, created_by, created_at FROM ticket_attachments
            WHERE ticket_id = %s AND deleted_at IS NULL ORDER BY created_at, id""", (ticket_id,))


@app.post("/tickets/{ticket_id}/attachments", status_code=201)
def add_attachment(ticket_id: UUID, body: AttachmentBody, user=Depends(caller)):
    if not body.storage_key.startswith(f"tickets/{ticket_id}/"):
        raise HTTPException(422, "storage_key must be under tickets/<ticket_id>/")
    with database() as db:
        row = ticket_for(db, ticket_id, user, lock=True)
        if row["created_by"] != user["sub"]:
            raise HTTPException(403, "Only creator may attach files")
        if row["status"] not in ("DRAFT", "SUBMITTED"):
            raise HTTPException(409, "Attachments only for DRAFT or SUBMITTED tickets")
        # The object must already be in the bucket; ask the gateway with the caller's token
        files_url = os.getenv("DATA_FILES_URL", "http://apisix:9080/api/files")
        try:
            head = httpx.head(f"{files_url}/{body.storage_key}",
                              headers={"Authorization": f"Bearer {user['token']}"}, timeout=10)
        except httpx.HTTPError as exc:
            raise HTTPException(503, "File storage unavailable") from exc
        if head.status_code != 200:
            raise HTTPException(422, "Uploaded file not found in storage")
        if one(db, "SELECT 1 AS found FROM ticket_attachments WHERE storage_key = %s",
               (body.storage_key,)):
            raise HTTPException(409, "storage_key already registered")
        attachment = one(db, """INSERT INTO ticket_attachments
            (ticket_id, storage_key, file_name, content_type, size_bytes, created_by)
            VALUES (%s,%s,%s,%s,%s,%s)
            RETURNING id, ticket_id, storage_key, file_name, content_type, size_bytes,
                      source, created_by, created_at""",
            (ticket_id, body.storage_key, body.file_name.strip(), body.content_type,
             body.size_bytes, user["sub"]))
        event(db, ticket_id, "ATTACH", user, row["status"], row["status"],
              {"attachment_id": attachment["id"], "file_name": attachment["file_name"],
               "storage_key": attachment["storage_key"], "size_bytes": attachment["size_bytes"]})
        return attachment


@app.get("/tickets/{ticket_id}/provenance")
def get_ticket_provenance(ticket_id: UUID, user=Depends(caller)):
    with database() as db:
        ticket = one(db, "SELECT * FROM tickets WHERE id = %s", (ticket_id,))
        if not ticket or not visible(ticket, user):
            raise HTTPException(404, "Ticket not found")
        events = many(db, """SELECT * FROM ticket_events WHERE ticket_id = %s
            ORDER BY occurred_at, id""", (ticket_id,))
        return {"ticket_id": ticket["id"], "source": ticket["source"],
                "created_by": ticket["created_by"], "created_at": ticket["created_at"],
                "updated_at": ticket["updated_at"], "deleted_at": ticket["deleted_at"],
                "reopen_count": sum(item["action"] == "REOPEN" for item in events),
                "events": events}


@app.patch("/tickets/{ticket_id}")
def edit_draft(ticket_id: UUID, body: DraftPatch, user=Depends(caller)):
    changes = body.model_dump(exclude_unset=True)
    if not changes or any(value is None for key, value in changes.items()
                          if key in ("title", "description")):
        raise HTTPException(422, "At least one valid field required")
    with database() as db:
        row = ticket_for(db, ticket_id, user, lock=True)
        if row["created_by"] != user["sub"]:
            raise HTTPException(403, "Only creator may edit draft")
        if row["status"] != "DRAFT":
            raise HTTPException(409, "Only draft may be edited")
        for field in ("title", "description"):
            if field in changes:
                changes[field] = changes[field].strip()
                if not changes[field]:
                    raise HTTPException(422, f"{field} cannot be blank")
        assignments = ", ".join(f"{field} = %s" for field in changes)
        updated = one(db, f"UPDATE tickets SET {assignments} WHERE id = %s RETURNING *",
                      list(changes.values()) + [ticket_id])
        event(db, ticket_id, "EDIT", user, "DRAFT", "DRAFT",
              {"changes": {field: {"before": row[field], "after": value}
                           for field, value in changes.items()}})
        return updated


@app.delete("/tickets/{ticket_id}", status_code=204)
def delete_draft(ticket_id: UUID, user=Depends(caller)):
    with database() as db:
        row = ticket_for(db, ticket_id, user, lock=True)
        if row["created_by"] != user["sub"]:
            raise HTTPException(403, "Only creator may delete draft")
        if row["status"] != "DRAFT":
            raise HTTPException(409, "Only draft may be deleted")
        execute(db, "UPDATE tickets SET deleted_at = now() WHERE id = %s", (ticket_id,))
        event(db, ticket_id, "DELETE", user, "DRAFT", "DRAFT")
    return Response(status_code=204)


@app.put("/tickets/{ticket_id}/rating")
def rate_ticket(ticket_id: UUID, body: RatingBody, user=Depends(caller)):
    with database() as db:
        row = ticket_for(db, ticket_id, user, lock=True)
        if row["created_by"] != user["sub"]:
            raise HTTPException(403, "Only creator may rate ticket")
        if row["status"] != "CLOSED":
            raise HTTPException(409, "Ticket must be closed")
        updated = one(db, """UPDATE tickets SET satisfaction_rating = %s
            WHERE id = %s RETURNING *""", (body.rating, ticket_id))
        event(db, ticket_id, "RATE", user, "CLOSED", "CLOSED",
              {"rating": {"before": row["satisfaction_rating"], "after": body.rating}})
        return updated


@app.post("/tickets/{ticket_id}/actions/{action}")
def transition(ticket_id: UUID, action: Action, body: ActionBody, user=Depends(caller)):
    expected = {Action.submit: "DRAFT", Action.accept: "SUBMITTED",
                Action.reject: "SUBMITTED", Action.assign: "SUBMITTED",
                Action.start: "ASSIGNED", Action.resolve: "IN_PROGRESS",
                Action.close: "RESOLVED", Action.reopen: "RESOLVED"}
    tasks = {Action.accept: "Task_Intake", Action.reject: "Task_Intake",
             Action.assign: "Task_Assign", Action.start: "Task_TechnicianAccept",
             Action.resolve: "Task_Repair", Action.close: "Task_Review",
             Action.reopen: "Task_Review"}
    target = {Action.submit: "SUBMITTED", Action.reject: "REJECTED",
              Action.assign: "ASSIGNED", Action.start: "IN_PROGRESS",
              Action.resolve: "RESOLVED", Action.close: "CLOSED",
              Action.reopen: "IN_PROGRESS"}
    audit_details = {}
    with database() as db:
        row = ticket_for(db, ticket_id, user, lock=True)
        if row["status"] != expected[action]:
            raise HTTPException(409, "Invalid ticket state")
        if action == Action.submit:
            if row["created_by"] != user["sub"]:
                raise HTTPException(403, "Only creator may submit")
            # asset_id stays optional so reporting still works when the asset system is down
            asset_location_id = (asset_location(row["asset_id"], user["token"])
                                 if row["asset_id"] else None)
            location_id = asset_location_id or row["location_id"]
            has_coordinates = (row.get("latitude") is not None and
                               row.get("longitude") is not None)
            if not row["category"] or not row["priority"]:
                raise HTTPException(422, "Category and priority required")
            if location_id and (asset_location_id or not has_coordinates):
                longitude, latitude = location_point(db, location_id)
                routing_source = "asset_location" if asset_location_id else "location_point"
            elif has_coordinates:
                longitude, latitude = row["longitude"], row["latitude"]
                location_id = None
                routing_source = "reporter_coordinates"
            else:
                raise HTTPException(422, "Location or coordinates required")
            site = spatial_site(db, longitude, latitude)
            process = flowable(user, "POST", "runtime/process-instances", {
                "processDefinitionKey": "dxlabHelpdeskRepair", "businessKey": str(ticket_id),
                "variables": variables(ticket_id=str(ticket_id), co_so=site,
                                       manager_candidate_group=f"manager_{site}",
                                       technician_candidate_group=f"technician_{site}")})
            updated = one(db, """UPDATE tickets SET status='SUBMITTED', co_so=%s,
                location_id=%s, latitude=%s, longitude=%s,
                workflow_instance_id=%s, submitted_at=now()
                WHERE id=%s RETURNING *""",
                (site, location_id, latitude, longitude, process["id"], ticket_id))
            audit_details = {"co_so": site, "asset_id": row["asset_id"],
                             "location_id": location_id, "routing_source": routing_source,
                             "latitude": latitude, "longitude": longitude,
                             "workflow_instance_id": process["id"]}
        else:
            manager = action in (Action.accept, Action.reject, Action.assign,
                                 Action.close, Action.reopen)
            if manager:
                if "ROLE_ADMIN" not in user["roles"] and not (
                    "ROLE_LAB_MANAGER" in user["roles"] and user["co_so"] == row["co_so"]
                ):
                    raise HTTPException(403, "Manager of ticket site required")
            elif not ("ROLE_ADMIN" in user["roles"] or
                      ("ROLE_TECHNICIAN" in user["roles"] and
                       user["co_so"] == row["co_so"] and row["assigned_to"] == user["sub"])):
                raise HTTPException(403, "Assigned technician required")
            task = current_task(user, row, tasks[action])
            if action in (Action.start, Action.resolve) and task.get("assignee") != user["username"]:
                raise HTTPException(403, "Workflow task belongs to another technician")
            values = {}
            changes = {}
            if action == Action.accept:
                values["intake_action"] = "ACCEPT"
            elif action in (Action.reject, Action.reopen):
                if not body.reason or not body.reason.strip():
                    raise HTTPException(422, "Reason required")
                if action == Action.reject:
                    values.update(intake_action="REJECT", rejection_reason=body.reason.strip())
                    changes.update(rejection_reason=body.reason.strip(), rejected_at="now()")
                else:
                    values.update(review_action="REOPEN", reopen_reason=body.reason.strip())
                    changes.update(resolved_at=None)
                audit_details["reason"] = body.reason.strip()
            elif action == Action.assign:
                if not body.technician_sub:
                    raise HTTPException(422, "technician_sub required")
                username = technician(body.technician_sub, row["co_so"])
                values["assigned_technician"] = username
                changes["assigned_to"] = body.technician_sub
                audit_details["technician_sub"] = body.technician_sub
                if body.priority:
                    changes["priority"] = body.priority.value
                    audit_details["priority"] = {"before": row["priority"],
                                                 "after": body.priority.value}
            elif action == Action.resolve:
                if not body.resolution_summary or not body.resolution_summary.strip():
                    raise HTTPException(422, "Resolution summary required")
                changes.update(resolution_summary=body.resolution_summary.strip(), resolved_at="now()")
                audit_details["resolution_summary"] = body.resolution_summary.strip()
            elif action == Action.close:
                values["review_action"] = "CLOSE"
                changes["closed_at"] = "now()"
            flowable(user, "POST", f"runtime/tasks/{task['id']}",
                     {"action": "complete", "variables": variables(**values)})
            if action in target:
                changes["status"] = target[action]
            if changes:
                parts = []
                params = []
                for field, value in changes.items():
                    parts.append(f"{field} = " + ("now()" if value == "now()" else "%s"))
                    if value != "now()":
                        params.append(value)
                updated = one(db, f"UPDATE tickets SET {', '.join(parts)} WHERE id = %s RETURNING *",
                              params + [ticket_id])
            else:
                updated = row
        event(db, ticket_id, "START_PROGRESS" if action == Action.start else action.value.upper(),
              user, row["status"], updated["status"], audit_details)
        if action in (Action.start, Action.close):
            event(db, ticket_id, "ASSET_STATUS_UPDATE_PENDING", user,
                  updated["status"], updated["status"],
                  {"asset_id": updated["asset_id"], "target_status": updated["status"],
                   "target_source": Source.SNIPE_IT.value})
    TRANSITIONS.labels(action.value, updated["status"], updated["co_so"] or "none").inc()
    published = (updated["status"] != row["status"]
                 and publish_status_changed(user, row["status"], updated, action.value))
    if action in (Action.start, Action.close):
        if published and updated["asset_id"]:
            # asset-sync consumes the event and keeps its own durable retry state
            record_asset_update_queued(user, updated)
        else:
            record_asset_status_update(user, updated)
    return updated
