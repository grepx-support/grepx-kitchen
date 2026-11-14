# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""PLAN_RUN - a driver's day: warehouse-out trips in delivery order, with arrival estimates."""
from grepx_service import RequestContext, new_key

from domain import clean_run
from dto import RunState
from .common import run_action, stamp


def handle(ctx: RequestContext) -> None:
    def body(fleet):
        run = {"run_id": new_key()[:12], "tenant_id": fleet.tenant, "state": RunState.PLANNED.value,
               **clean_run({k: ctx.get(k) for k in ("date", "start_time", "name", "vehicle", "driver_id", "driver_name",
                                                     "drive_minutes", "service_minutes")}),
               "planned_by": ctx.text("actor_name"), "planned_at": stamp()}
        run["stops"] = fleet.stops_for(ctx.get("delivery_ids"))
        return fleet.save(run)
    run_action(ctx, body)
