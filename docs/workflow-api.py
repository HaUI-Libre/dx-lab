#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
# SPDX-License-Identifier: Apache-2.0
"""Run the success, reject and reopen BPMN paths through APISIX."""

import json
import os
import subprocess
import sys
import urllib.parse
import uuid


GW = f"http://localhost:{os.getenv('GATEWAY_PORT', '9080')}/api/workflow"
KC = (f"http://localhost:{os.getenv('KEYCLOAK_PORT', '8080')}/realms/"
      f"{os.getenv('KEYCLOAK_REALM', 'dxlab')}/protocol/openid-connect/token")


def call(url, token=None, payload=None, expected=200, form=False):
    command = ["curl", "--silent", "--show-error", "--max-time", "15",
               "--write-out", "\n%{http_code}", "--url", url]
    if token:
        command.extend(["--header", "Authorization: Bearer " + token])
    if payload is not None:
        if form:
            data = urllib.parse.urlencode(payload).encode()
            content_type = "application/x-www-form-urlencoded"
        else:
            data = json.dumps(payload).encode()
            content_type = "application/json"
        command.extend(["--header", "Content-Type: " + content_type,
                        "--request", "POST", "--data-binary", "@-"])
    else:
        data = b""
    result = subprocess.run(command, input=data, capture_output=True, check=False)
    if result.returncode:
        raise RuntimeError(f"curl thất bại ở {url}: {result.stderr.decode(errors='replace')}")
    body, code = result.stdout.rsplit(b"\n", 1)
    status = int(code)
    assert status == expected, f"{url}: HTTP {status}, cần {expected}: {body[:500]!r}"
    return json.loads(body) if body else None


def variables(**values):
    return [{"name": key, "value": value} for key, value in values.items()]


def task(token, instance, key, assignee=None):
    query = urllib.parse.urlencode({"processInstanceId": instance})
    result = call(f"{GW}/runtime/tasks?{query}", token)
    tasks = result["data"]
    assert result["total"] == 1 and len(tasks) == 1, f"{instance}: cần đúng một task, nhận {tasks}"
    current = tasks[0]
    assert current["taskDefinitionKey"] == key, f"{instance}: task {current['taskDefinitionKey']}, cần {key}"
    if assignee:
        assert current["assignee"] == assignee, f"{instance}: sai assignee"
    print(f"  {key}: {current['id']}")
    return current["id"]


def complete(token, task_id, **values):
    call(f"{GW}/runtime/tasks/{task_id}", token,
         {"action": "complete", "variables": variables(**values)})


def history(token, instance, expected_keys):
    query = urllib.parse.urlencode({"processInstanceId": instance, "size": 100})
    result = call(f"{GW}/history/historic-task-instances?{query}", token)
    assert result["total"] == len(expected_keys), f"{instance}: history thiếu task"
    tasks = sorted(result["data"], key=lambda item: (item["startTime"], int(item["id"])))
    actual = [item["taskDefinitionKey"] for item in tasks]
    assert actual == expected_keys, f"{instance}: thứ tự history {actual}, cần {expected_keys}"
    assert all(item["endTime"] for item in tasks), f"{instance}: task lịch sử chưa hoàn tất"
    historic = call(f"{GW}/history/historic-process-instances/{instance}", token)
    assert historic["endTime"], f"{instance}: process chưa kết thúc"
    print(f"  history: {' -> '.join(actual)}; process đã kết thúc")


def run(token, scenario):
    ticket = str(uuid.uuid4())
    started = call(f"{GW}/runtime/process-instances", token, {
        "processDefinitionKey": "dxlabHelpdeskRepair",
        "businessKey": ticket,
        "variables": variables(ticket_id=ticket, co_so="CS1",
                               manager_candidate_group="manager_CS1",
                               technician_candidate_group="technician_CS1"),
    }, expected=201)
    instance = started["id"]
    print(f"{scenario}: instance {instance}, ticket {ticket}")
    intake = task(token, instance, "Task_Intake")
    if scenario == "reject":
        complete(token, intake, intake_action="REJECT", rejection_reason="Thiếu thông tin thiết bị")
        history(token, instance, ["Task_Intake"])
        return
    complete(token, intake, intake_action="ACCEPT")
    assign = task(token, instance, "Task_Assign")
    complete(token, assign, assigned_technician="kythuatvien")
    accept = task(token, instance, "Task_TechnicianAccept", "kythuatvien")
    complete(token, accept)
    repair = task(token, instance, "Task_Repair", "kythuatvien")
    complete(token, repair)
    review = task(token, instance, "Task_Review")
    expected = ["Task_Intake", "Task_Assign", "Task_TechnicianAccept",
                "Task_Repair", "Task_Review"]
    if scenario == "reopen":
        complete(token, review, review_action="REOPEN", reopen_reason="Chưa khắc phục triệt để")
        repair = task(token, instance, "Task_Repair", "kythuatvien")
        complete(token, repair)
        review = task(token, instance, "Task_Review")
        expected.extend(["Task_Repair", "Task_Review"])
    complete(token, review, review_action="CLOSE")
    history(token, instance, expected)


def main():
    scenarios = sys.argv[1:] or ["success", "reject", "reopen"]
    assert all(item in ("success", "reject", "reopen") for item in scenarios), "Dùng success, reject, reopen"
    auth = call(KC, payload={"grant_type": "password",
                             "client_id": os.getenv("KEYCLOAK_CLIENT_ID", "dxlab-app"),
                             "client_secret": os.environ["KEYCLOAK_CLIENT_SECRET"],
                             "username": "quantri", "password": os.environ["DEMO_USER_PASSWORD"]},
                form=True)
    token = auth["access_token"]
    for scenario in scenarios:
        run(token, scenario)


if __name__ == "__main__":
    try:
        main()
    except (AssertionError, KeyError, ValueError, RuntimeError) as error:
        print(f"FAIL workflow API: {error}", file=sys.stderr)
        sys.exit(1)
