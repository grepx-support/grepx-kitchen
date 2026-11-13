# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Step 2 - past days, so targets, reorder suggestions and costs have history to work from.

Screens only ever record today, so the stock moves of past days go to stock-service as dated requests (the same
requests the site sends, with a date). Closings use the site, which accepts a past date. Each day: buy every third
day, send ingredients to the kitchen, cook, bring the food to the warehouse, deliver to the stores and the truck,
then each of them closes: counts what is left and enters the takings.
"""
from __future__ import annotations

import math
import random
import time
from datetime import date, timedelta

import grepx_contracts as gc
from grepx_service import RequestClient
from nexus_api import NexusClient

from setup import staff


class Stock:
    """Dated stock requests as one of the demo staff."""

    def __init__(self, ids: dict, d):
        self.ids, self.d = ids, d
        self.client = RequestClient(NexusClient("demo-seed"), "demo-seed", timeout=30)

    def do(self, action: str, role: str, day: date, **fields) -> str:
        name, email = staff(self.d, role)
        v = self.client.call(gc.stock.REQUESTS, gc.stock.SERVICE, {"action": action, "tenant_id": self.ids["tenant"], "date": day.isoformat(),
                                                                   "actor_id": self.ids["user"][email], "actor_name": name, **fields})
        if not v.ok:
            raise RuntimeError(f"{action} on {day}: {v.reason}")
        return v.key

    def lines(self, qty: dict) -> list[dict]:
        return [{"item_id": self.ids["item"][k], "qty": round(q, 2)} for k, q in qty.items() if q > 0]


def plan_for(d, rng) -> dict:
    """What each place sells today (the usual amount, give or take a quarter)."""
    return {place: {p: max(0, round(n * rng.uniform(0.75, 1.25))) for p, n in sold.items()} for place, sold in d.DAILY_SALES.items()}


def cook(d, made_needed: dict) -> tuple[dict, dict]:
    """Batches for the day: finished goods made, ingredients used."""
    made, used = {}, {}
    for product, need in made_needed.items():
        output, parts = d.RECIPES[product]
        batches = max(0, math.ceil(need / output))
        if not batches:
            continue
        made[product] = batches * output
        for k, q in parts.items():
            used[k] = used.get(k, 0) + q * batches
    return made, used


def run(site, d, ids: dict, days: int, say, seed: int = 7) -> None:
    rng, stock = random.Random(seed), Stock(ids, d)
    p = ids["place"]
    spare = {prod: 0.0 for prod in d.PRICE}                  # cooked food still at the warehouse
    for n in range(days, 0, -1):
        day = date.today() - timedelta(days=n)
        sales = plan_for(d, rng)
        sent = {prod: sum(s[prod] for s in sales.values()) * 1.1 for prod in d.PRICE}
        made, used = cook(d, {prod: max(0, sent[prod] - spare[prod]) for prod in d.PRICE})   # cook only what the warehouse lacks
        spare = {prod: spare[prod] + made.get(prod, 0) - sent[prod] for prod in d.PRICE}
        if n % 3 == days % 3:                                    # buy for three days
            for sup in {it[5] for it in d.ITEMS if it[5]}:
                buy = {k: used.get(k, 0) * 3.3 for k, _, kind, _, _, s, _ in d.ITEMS if s == sup and kind == "ingredient"}
                if sup == d.PACKAGING[0]:
                    buy = d.PACKAGING[1]
                if any(buy.values()):
                    stock.do("RECEIVE", "warehouse", day, location_id=p["wh"], lines=stock.lines(buy), supplier_id=ids["supplier"][sup], note="Supplier delivery")
        if made:
            stock.do("SEND", "warehouse", day, from_location_id=p["wh"], to_location_id=p["kit"], lines=stock.lines(used))
            stock.do("USE", "kitchen", day, location_id=p["kit"], lines=stock.lines(used))
            stock.do("PRODUCE", "kitchen", day, location_id=p["kit"], lines=stock.lines(made))
            stock.do("TRANSFER", "kitchen", day, from_location_id=p["kit"], to_location_id=p["wh"], lines=stock.lines(made))
        for place in d.SELLERS:
            trip = stock.do("SEND", "warehouse", day, from_location_id=p["wh"], to_location_id=p[place],
                            lines=stock.lines({prod: q * 1.1 for prod, q in sales[place].items()}))
            stock.do("DELIVERED", "delivery", day, delivery_id=trip)
            close(site, d, ids, place, day, sales[place], rng)
        say(f"{day}: made {sum(made.values())}, sold {sum(sum(s.values()) for s in sales.values())} across {len(d.SELLERS)} places")


def close(site, d, ids: dict, place: str, day: date, sold: dict, rng) -> None:
    """The evening closing at one place: count what is left (expected minus what sold) and enter the takings."""
    loc = ids["place"][place]
    name, email = staff(d, "closing")
    form = site.get(f"/closing/form?location_id={loc}", email)
    by_id = {v: k for k, v in ids["item"].items()}
    counts = [{"item_id": l["item_id"], "qty": max(0, round(l["expected"] - sold.get(by_id.get(l["item_id"]), 0)))} for l in form["lines"]]
    takings = sum(q * d.PRICE[prod] for prod, q in sold.items())
    issue = rng.choice(d.ISSUES)
    site.post("/closing", {"location_id": loc, "date": day.isoformat(), "staff_name": name, "issues": issue, "counts": counts,
                           "sales": {"Sales": round(takings * 0.85, 2), "Other sales": round(takings * 0.15, 2)}}, email)
    time.sleep(0.8)                                              # the count reaches stock and costing before the next day
