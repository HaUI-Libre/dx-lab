<!--
SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
SPDX-License-Identifier: Apache-2.0
-->

# DX-Lab HaUI: a digital operations hub on DX-OS Open-Core

[Tiếng Việt](README.md) · English summary

> The Vietnamese [README.md](README.md) is the reference document. This page is a short
> summary for readers who do not read Vietnamese; when the two differ, the Vietnamese
> version is correct.

## What it is

DX-Lab is a reference implementation of **DX-OS Open-Core** for managing IT equipment in
university labs. The sample application, **DX-Helpdesk**, lets students report broken
devices, routes each ticket to the right campus (3 campuses of Hanoi University of
Industry), lets lab managers assign technicians and accept the repair, and updates the
asset status in the customer's existing asset system (simulated with Snipe-IT).

Main features, all running in the current release:

- Single sign-on for every role (Keycloak, OpenID Connect).
- "My devices" read from the asset system; report a fault with photos; report by location
  when the asset system is down.
- Campus routing with PostGIS from the asset location or the reporter's coordinates.
- BPMN workflow on Flowable: intake, rejection with a reason, assignment to a technician of
  the same campus, repair report, acceptance, reopening with a reason.
- Asset status updates in Snipe-IT through NATS JetStream events.
- Ticket history and provenance, readable ticket codes `DXL-NNNN`, statistics per campus.
- Category and priority suggestions (scikit-learn) with a keyword fallback; the user
  always confirms or edits them.
- Monitoring with Prometheus and Grafana.

## Architecture

```
Layer 3  Business application   DX-Helpdesk (Nuxt 4)
Layer 2  H-P-D-I capabilities   [H] portal, users, documents  [P] workflow, queues
                                [D] Data API, provenance, stats [I] classification
Layer 1  DX-OS Open-Core        Keycloak · Apache APISIX · PostgreSQL + PostGIS
         (headless, no UI)      SeaweedFS · Flowable · NATS JetStream
Outside DX-OS                   customer asset system: Snipe-IT + MariaDB
```

Every call from layers 2 and 3 goes through the API gateway with a Keycloak token. Details
(in Vietnamese): [docs/architecture.md](docs/architecture.md).

## Requirements

- Docker Engine 24+ and the Docker Compose plugin v2.17+ (Docker Desktop is not needed).
- Git, `make`, `curl`, `bash`, Python 3 (standard library only).
- 16 GB RAM recommended.
- Windows: use WSL2 and clone inside the WSL file system (for example `~/dx-lab`).

To build the app, the APISIX plugin, the Data API and the classifier from source without
Docker, see [docs/build-from-source.md](docs/build-from-source.md).

## Quick start

```bash
git clone https://github.com/HaUI-Libre/dx-lab.git
cd dx-lab
make env      # creates .env with random secrets; never commit this file
make up       # core services and the app; waits until healthy, deploys the BPMN model
make smoke    # checks gateway auth, tokens, workflow, files, ticket lifecycle, SSO
```

For the full demo (asset system, events, monitoring) and sample data:

```bash
make demo     # every profile; the login page shows "try as role" buttons
make seed     # sample tickets and guide documents
```

Open http://localhost:3000. All demo accounts share the password `DEMO_USER_PASSWORD`
from `.env` (see `.env.example`).

| Role | Username | Can do |
|---|---|---|
| Student | `sinhvien` | Report faults, follow own tickets, rate after closing |
| Lab manager, campus 1 | `truongphong` | Accept or reject, assign, accept the repair, reopen |
| Technician, campus 1 | `kythuatvien` | Take the job, write the repair report, mark as done |
| Administrator | `quantri` | See all three campuses |

Other services: API gateway http://localhost:9080, Keycloak http://localhost:8080,
Snipe-IT http://127.0.0.1:8081 and Grafana http://127.0.0.1:3001 (with `make demo`).
Every port listens on `127.0.0.1` only.

Sample tickets created by `make seed` are for viewing only; workflow actions on them return
409 because they are not linked to a workflow instance. Use a new ticket to walk through
the workflow.

## Checks

| Command | What it checks |
|---|---|
| `make check` | License information on every file (REUSE) |
| `make test` | Python tests in `tests/`, no running stack needed |
| `make smoke` | On a running stack: gateway 401/403/200, tokens, workflow, files, app pages |
| `make smoke-assets` | After `make demo`: Snipe-IT devices and labels, events over NATS and SSE |
| `make test-e2e` | After `make demo`: the full demo chain and its alternative branches |

## Contributing

Read [CONTRIBUTING.md](CONTRIBUTING.md) (Vietnamese). Issues and pull requests in English
are welcome. Planned work is in [ROADMAP.md](ROADMAP.md); newcomers can start with an issue
labelled
[`good first issue`](https://github.com/HaUI-Libre/dx-lab/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22).

## License

Apache License 2.0, see [LICENSE](LICENSE) and [NOTICE](NOTICE). Third-party components and
their licenses are listed in [docs/dependencies.md](docs/dependencies.md); services such as
Snipe-IT (AGPL-3.0) and Grafana (AGPL-3.0) run as separate services and keep their own
licenses ([docs/license-decision.md](docs/license-decision.md)).
