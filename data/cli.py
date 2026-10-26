# SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
# SPDX-License-Identifier: Apache-2.0

import os

import uvicorn


def serve():
    uvicorn.run("dxlab_data.app:app", host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
