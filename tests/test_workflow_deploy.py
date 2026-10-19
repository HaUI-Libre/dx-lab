# SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
# SPDX-License-Identifier: Apache-2.0
"""Exercise the deploy decision without a Flowable daemon."""

import pathlib
import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "core" / "workflow"))
os.environ.setdefault("FLOWABLE_URL", "http://flowable:8080/flowable-rest/service")
import deploy  # noqa: E402


class DeployTests(unittest.TestCase):
    def test_unchanged_definition_does_not_post(self):
        source = deploy.BPMN.read_bytes()
        calls = []

        def fake(path, method="GET", data=None, content_type=None):
            calls.append((method, path))
            if "process-definitions?" in path:
                return 200, b'{"data":[{"id":"definition:1:1","version":1}]}'
            if path.endswith("/resourcedata"):
                return 200, source
            raise AssertionError(path)

        with patch.object(deploy, "ready"), patch.object(deploy, "request", side_effect=fake):
            deploy.deploy()
        self.assertFalse(any(method == "POST" for method, _ in calls))

    def test_changed_definition_creates_new_version(self):
        source = deploy.BPMN.read_bytes()
        posted = False

        def fake(path, method="GET", data=None, content_type=None):
            nonlocal posted
            if "process-definitions?" in path:
                version = 2 if posted else 1
                return 200, ('{"data":[{"id":"definition:%s:1","version":%s}]}' % (version, version)).encode()
            if path.endswith("/resourcedata"):
                return 200, source if posted else b"old BPMN"
            if path == "/repository/deployments" and method == "POST":
                self.assertIn(source, data)
                self.assertIn("multipart/form-data", content_type)
                posted = True
                return 201, b'{"id":"deployment-2"}'
            raise AssertionError(path)

        with patch.object(deploy, "ready"), patch.object(deploy, "request", side_effect=fake):
            deploy.deploy()
        self.assertTrue(posted)


if __name__ == "__main__":
    unittest.main()
