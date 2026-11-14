# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""kitchen-bff - the kitchen product's API (web + mobile) on the shared grepx_bff core. Wiring only."""
from __future__ import annotations

import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent
sys.path.insert(0, str(SRC))

from grepx_bff import Gateway, create_app as build  # noqa: E402
from grepx_config import load_config  # noqa: E402
from nexus_api import NexusClient  # noqa: E402

from routers import ROUTERS  # noqa: E402

cfg = load_config(SRC.parent / "config")
ROOT = Path(cfg.workspace)


def create_app(gw: Gateway):
    """JSON API at /api/v1; the shared web shell (web/, from grepx-platform) with the kitchen screens (apps/web)."""
    from product_copy import COPY
    from grepx_bff import register_copy
    register_copy(COPY)
    return build(gw, ROUTERS, cfg.get("api_title") or "Kitchen API", web_dir=ROOT / "web", product=cfg.get("product", "kitchen"),
                 product_dir=ROOT / "apps" / "web")


if __name__ == "__main__":
    from grepx_web_bootstrap import run_server
    from nexus_api import Heartbeat
    client = NexusClient(cfg.service_name, host=cfg.nexus.host, port=cfg.nexus.port)
    Heartbeat(NexusClient(f"{cfg.service_name}-heartbeat", host=cfg.nexus.host, port=cfg.nexus.port), cfg.service_name).start()
    run_server(create_app(Gateway(client, cfg)), service=cfg.service_name, host=(cfg.get("web") or {}).get("bind", "0.0.0.0"))
