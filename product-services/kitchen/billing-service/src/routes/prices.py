# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""SET_PRICE_BREAKS (an item's quantity breaks), PRICE (one item for one customer and quantity) and PRICE_LIST (every
item you sell: list price, breaks, and the customers with their own price for it)."""
from grepx_service import RequestContext

from domain import clean_breaks, price_for
from dto import ReasonCode, Table
from .common import Stop, run


def set_breaks(ctx: RequestContext) -> None:
    def body(books):
        item_id = ctx.text("item_id")
        if item_id not in books.items():
            raise Stop(ReasonCode.UNKNOWN_ITEM)
        return {"breaks": books.save(Table.PRICE_BREAKS.value, item_id, {"item_id": item_id, "breaks": clean_breaks(ctx.get("breaks"))})["breaks"]}
    run(ctx, body)


def price(ctx: RequestContext) -> None:
    def body(books):
        item = books.items().get(ctx.text("item_id"))
        if item is None:
            raise Stop(ReasonCode.UNKNOWN_ITEM)
        customer = books.customer(ctx.text("customer_id")) if ctx.text("customer_id") else {}
        return price_for(item, ctx.get("qty") or 1, customer.get("pricing"), books.breaks().get(item["_key"]))
    run(ctx, body)


def price_list(ctx: RequestContext) -> None:
    def body(books):
        breaks = books.breaks()
        customers = [c for c in books.customers() if c.get("active", True)]
        rows = [{"item_id": k, "name": i.get("name", ""), "unit": i.get("unit", ""), "price": i.get("price") or 0, "breaks": breaks.get(k, []),
                 "customers": [{"customer_id": c["customer_id"], "name": c["name"], "price": (c.get("pricing") or {}).get("prices", {}).get(k)}
                               for c in customers if k in ((c.get("pricing") or {}).get("prices") or {})]}
                for k, i in books.items().items() if i.get("kind") == "finished" or i.get("price")]
        return {"items": sorted(rows, key=lambda r: r["name"].lower()),
                "discounts": [{"customer_id": c["customer_id"], "name": c["name"], "discount_pct": (c.get("pricing") or {}).get("discount_pct", "0")}
                              for c in customers if float((c.get("pricing") or {}).get("discount_pct") or 0)]}
    run(ctx, body)
