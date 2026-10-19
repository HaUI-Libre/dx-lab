#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
# SPDX-License-Identifier: Apache-2.0
"""Deploy the BPMN only when the latest Flowable definition differs."""

import base64
import json
import os
import pathlib
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid


BASE = os.environ["FLOWABLE_URL"].rstrip("/")
PROCESS_KEY = "dxlabHelpdeskRepair"
BPMN = pathlib.Path(__file__).with_name("helpdesk.bpmn20.xml")


def request(path, method="GET", data=None, content_type=None):
    user = os.environ["FLOWABLE_ADMIN_USER"]
    password = os.environ["FLOWABLE_ADMIN_PASSWORD"]
    basic = base64.b64encode(f"{user}:{password}".encode()).decode()
    headers = {"Authorization": f"Basic {basic}"}
    if content_type:
        headers["Content-Type"] = content_type
    req = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as error:
        body = error.read(1024).decode("utf-8", errors="replace")
        raise RuntimeError(f"Flowable {method} {path}: HTTP {error.code}: {body}") from error


def ready():
    deadline = time.monotonic() + 180
    while time.monotonic() < deadline:
        try:
            status, _ = request("/repository/process-definitions?size=1")
            if status == 200:
                return
        except (urllib.error.URLError, TimeoutError):
            pass
        time.sleep(3)
    raise RuntimeError("Flowable REST chưa sẵn sàng sau 180 giây")


def multipart(payload):
    boundary = "dxlab-" + uuid.uuid4().hex
    name = BPMN.name
    body = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"{name}\"; "
            f"filename=\"{name}\"\r\nContent-Type: application/xml\r\n\r\n").encode()
    body += payload + f"\r\n--{boundary}--\r\n".encode()
    return body, f"multipart/form-data; boundary={boundary}"


def deploy():
    ready()
    source = BPMN.read_bytes()
    query = urllib.parse.urlencode({"key": PROCESS_KEY, "latest": "true"})
    _, raw = request("/repository/process-definitions?" + query)
    definitions = json.loads(raw)["data"]
    if len(definitions) > 1:
        raise RuntimeError("Có nhiều process definition mới nhất cho cùng process key")
    if definitions:
        definition = definitions[0]
        resource_path = "/repository/process-definitions/" + urllib.parse.quote(definition["id"], safe="") + "/resourcedata"
        _, deployed = request(resource_path)
        if deployed == source:
            print(f"BPMN {PROCESS_KEY} v{definition['version']} không đổi; bỏ qua deploy")
            return
    body, content_type = multipart(source)
    status, raw = request("/repository/deployments", "POST", body, content_type)
    if status != 201:
        raise RuntimeError(f"Deploy trả HTTP {status}, cần 201")
    deployment = json.loads(raw)
    _, raw = request("/repository/process-definitions?" + query)
    definitions = json.loads(raw)["data"]
    if len(definitions) != 1:
        raise RuntimeError("Deploy thành công nhưng không tìm thấy đúng process definition")
    definition = definitions[0]
    _, deployed = request("/repository/process-definitions/" + urllib.parse.quote(definition["id"], safe="") + "/resourcedata")
    if deployed != source:
        raise RuntimeError("BPMN đang chạy khác nội dung vừa deploy")
    print(f"Đã deploy {PROCESS_KEY} v{definition['version']} (deployment {deployment['id']})")


if __name__ == "__main__":
    try:
        deploy()
    except (RuntimeError, KeyError, ValueError, urllib.error.URLError) as error:
        print(f"Lỗi deploy BPMN: {error}", file=sys.stderr)
        sys.exit(1)
