# SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
# SPDX-License-Identifier: Apache-2.0

"""DX-Helpdesk Data API. Flowable owns tasks; this service owns ticket data."""

import json
import os
from contextlib import contextmanager
from enum import Enum
from uuid import UUID

import httpx
import jwt
import pg8000.dbapi
from fastapi import Depends, FastAPI, Header, HTTPException, Query, Response
from pydantic import BaseModel, ConfigDict, Field


app = FastAPI(title="DX-Lab Data API", version="0.3.0", root_path="/api/data")
ROLES = {"ROLE_STUDENT", "ROLE_TECHNICIAN", "ROLE_LAB_MANAGER", "ROLE_ADMIN"}
ISSUER = os.getenv("KEYCLOAK_ISSUER", "http://localhost:8080/realms/dxlab")
JWKS_URL = os.getenv("KEYCLOAK_JWKS_URL", "http://keycloak:8080/realms/dxlab/protocol/openid-connect/certs")
JWKS = jwt.PyJWKClient(JWKS_URL, cache_jwk_set=True, lifespan=300)
FLOWABLE_URL = os.getenv("DATA_WORKFLOW_URL", "http://apisix:9080/api/workflow/data")


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
    asset_id: int | None = Field(default=None, gt=0)


class DraftPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, min_length=1)
    category: Category | None = None
    priority: Priority | None = None
    location: str | None = None
    location_id: int | None = Field(default=None, gt=0)
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
                                  timeout=5)
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
    with database() as db:
        event(db, ticket["id"], f"ASSET_STATUS_UPDATE_{outcome}", user,
              ticket["status"], ticket["status"], details,
              source=Source.SNIPE_IT if outcome == "SUCCEEDED" else Source.DX_HELPDESK)


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


def technician(sub, site):
    """Resolve a Keycloak subject server-side; never trust a UI supplied site."""
    try:
        sub = str(UUID(sub))
    except ValueError as exc:
        raise HTTPException(422, "Invalid technician_sub") from exc
    base = os.getenv("KEYCLOAK_INTERNAL_URL", "http://keycloak:8080")
    realm = os.getenv("KEYCLOAK_REALM", "dxlab")
    try:
        token_response = httpx.post(f"{base}/realms/master/protocol/openid-connect/token",
                                    data={"grant_type": "password", "client_id": "admin-cli",
                                          "username": os.environ["KEYCLOAK_ADMIN"],
                                          "password": os.environ["KEYCLOAK_ADMIN_PASSWORD"]}, timeout=10)
        token_response.raise_for_status()
        headers = {"Authorization": f"Bearer {token_response.json()['access_token']}"}
        user_response = httpx.get(f"{base}/admin/realms/{realm}/users/{sub}",
                                  headers=headers, timeout=10)
        user_response.raise_for_status()
        roles_response = httpx.get(f"{base}/admin/realms/{realm}/users/{sub}/role-mappings/realm/composite",
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


@app.post("/tickets", status_code=201)
def create_ticket(body: Draft, response: Response, user=Depends(caller)):
    if not body.title.strip() or not body.description.strip():
        raise HTTPException(422, "Title and description cannot be blank")
    with database() as db:
        row = one(db, """INSERT INTO tickets
            (title, description, category, priority, location, location_id, asset_id, created_by)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s) RETURNING *""",
            (body.title.strip(), body.description.strip(), body.category, body.priority,
             body.location, body.location_id, body.asset_id, user["sub"]))
        event(db, row["id"], "CREATE_DRAFT", user, None, "DRAFT",
              {"title": row["title"], "category": row["category"],
               "priority": row["priority"], "asset_id": row["asset_id"],
               "location_id": row["location_id"]})
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
        clauses.append("(title ILIKE %s OR description ILIKE %s)")
        params += [f"%{q}%", f"%{q}%"]
    where = " AND ".join(clauses)
    with database() as db:
        total = one(db, f"SELECT count(*) AS count FROM tickets WHERE {where}", params)["count"]
        items = many(db, f"SELECT * FROM tickets WHERE {where} ORDER BY created_at DESC, id DESC "
                     "LIMIT %s OFFSET %s", params + [page_size, (page - 1) * page_size])
    return {"items": items, "total": total, "page": page, "page_size": page_size}


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
            if not row["category"] or not row["priority"] or not row["asset_id"] or not row["location_id"]:
                raise HTTPException(422, "Category, priority, asset_id and location_id required")
            site = one(db, "SELECT co_so FROM site_locations WHERE location_id = %s",
                       (row["location_id"],))
            if not site:
                raise HTTPException(422, "Unknown asset location")
            site = site["co_so"]
            process = flowable(user, "POST", "runtime/process-instances", {
                "processDefinitionKey": "dxlabHelpdeskRepair", "businessKey": str(ticket_id),
                "variables": variables(ticket_id=str(ticket_id), co_so=site,
                                       manager_candidate_group=f"manager_{site}",
                                       technician_candidate_group=f"technician_{site}")})
            updated = one(db, """UPDATE tickets SET status='SUBMITTED', co_so=%s,
                workflow_instance_id=%s, submitted_at=now() WHERE id=%s RETURNING *""",
                (site, process["id"], ticket_id))
            audit_details = {"co_so": site, "asset_id": row["asset_id"],
                             "location_id": row["location_id"],
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
    if action in (Action.start, Action.close):
        record_asset_status_update(user, updated)
    return updated
