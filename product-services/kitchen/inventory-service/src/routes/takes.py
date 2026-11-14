# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Stock take: START_TAKE freezes what the system expects, COUNT_TAKE records counts, FINISH_TAKE corrects stock to the
counts (stock-service ADJUST with the take as reason) and keeps the variance, CANCEL_TAKE drops it."""
import grepx_contracts as gc
from grepx_service import RequestContext, new_key, now_iso, state_of

from domain import variance
from dto import ReasonCode, Table, TakeState
from .common import Stop, run


def _take(stock, ctx, open_only=True) -> dict:
    take = stock.mine(Table.STOCK_TAKES.value, ctx.text("take_id"), ReasonCode.UNKNOWN_TAKE)
    if open_only and take.get("state") != TakeState.OPEN.value:
        raise Stop(ReasonCode.TAKE_CLOSED)
    return take


def start(ctx: RequestContext) -> None:
    def body(stock):
        place = stock.mine(gc.business.LOCATIONS, ctx.text("location_id"), ReasonCode.UNKNOWN_LOCATION)
        if any(t.get("location_id") == place["_key"] for t in ctx.read.accepted(Table.STOCK_TAKES.value, tenant_id=stock.tenant,
                                                                                  state=TakeState.OPEN.value)):
            raise Stop(ReasonCode.TAKE_OPEN_HERE)
        items = stock.items()
        held = {l["item_id"]: float(l.get("qty") or 0) for l in stock.levels(place["_key"])}
        lines = [{"item_id": i, "name": it.get("name", ""), "unit": it.get("unit", ""), "expected": held.get(i, 0.0), "counted": None}
                 for i, it in sorted(items.items(), key=lambda kv: (kv[1].get("sort", 10**6), kv[1].get("name", "")))
                 if it.get("active", True) and (i in held or ctx.get("all_items"))]
        take_id = new_key()[:12]
        row = {"take_id": take_id, "tenant_id": stock.tenant, "location_id": place["_key"], "location_name": place.get("name", ""),
               "state": TakeState.OPEN.value, "blind": bool(ctx.get("blind")), "lines": lines, "started_at": now_iso(),
               "started_by": ctx.text("actor_name")}
        ctx.emitter.submit(Table.STOCK_TAKES.value, take_id, "ACCEPTED", row)
        return {"take": row}
    run(ctx, body)


def count(ctx: RequestContext) -> None:
    def body(stock):
        take = _take(stock, ctx)
        counted = {}
        for line in ctx.get("lines") or []:
            try:
                q = None if line.get("qty") in (None, "") else float(line["qty"])
            except (TypeError, ValueError):
                raise Stop(ReasonCode.INVALID_QUANTITY)
            if q is not None and q < 0:
                raise Stop(ReasonCode.INVALID_QUANTITY)
            counted[str(line.get("item_id"))] = q
        lines = [{**l, "counted": counted.get(l["item_id"], l.get("counted"))} for l in take["lines"]]
        row = {**state_of(take), "lines": lines}
        ctx.emitter.submit(Table.STOCK_TAKES.value, take["_key"], "ACCEPTED", row)
        return {"take": row}
    run(ctx, body)


def finish(ctx: RequestContext) -> None:
    def body(stock):
        take = _take(stock, ctx)
        lines = variance(take["lines"], stock.costs())
        if not lines:
            raise Stop(ReasonCode.NOTHING_COUNTED)
        changed = [l for l in lines if l["variance"]]
        if changed:
            ctx.request(gc.stock.REQUESTS, f"take-{take['_key']}",
                        {"action": gc.stock.StockAction.ADJUST.value, "tenant_id": stock.tenant, "location_id": take["location_id"],
                         "lines": [{"item_id": l["item_id"], "qty": l["counted"]} for l in changed], "ref": take["_key"],
                         "note": f"Stock take {take['started_at'][:10]}", "actor_id": ctx.text("actor_id"), "actor_name": ctx.text("actor_name")},
                        gc.stock.SERVICE)
        row = {**state_of(take), "state": TakeState.DONE.value, "lines": lines, "finished_at": now_iso(), "finished_by": ctx.text("actor_name"),
               "variance_value": round(sum(l["value"] for l in lines), 2), "lines_counted": len(lines), "lines_changed": len(changed)}
        ctx.emitter.submit(Table.STOCK_TAKES.value, take["_key"], "ACCEPTED", row)
        return {"take": row}
    run(ctx, body)


def cancel(ctx: RequestContext) -> None:
    def body(stock):
        take = _take(stock, ctx)
        row = {**state_of(take), "state": TakeState.CANCELLED.value}
        ctx.emitter.submit(Table.STOCK_TAKES.value, take["_key"], "ACCEPTED", row)
        return {"take": row}
    run(ctx, body)
