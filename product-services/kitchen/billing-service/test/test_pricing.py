# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""billing-service prices: a customer's own price, quantity breaks, standing discount, charge lines kept apart."""
import pytest

from domain import clean_breaks, clean_pricing, price_for
from test_quotes import call, h  # noqa: F401  (h: the shared fixture with a "taco" item)


def test_price_rules():
    taco = {"_key": "taco", "price": 10}
    breaks = clean_breaks([{"min_qty": 50, "price": 8}, {"min_qty": 10, "price": 9}])
    assert [b["min_qty"] for b in breaks] == ["10", "50"]
    assert price_for(taco, 5, None, breaks) == {"unit_price": "10", "discount": "0", "source": "list"}
    assert price_for(taco, 60, {"discount_pct": "5", "prices": {}}, breaks) == {"unit_price": "8", "discount": "5", "source": "break"}
    assert price_for(taco, 60, clean_pricing({"discount_pct": 5, "prices": {"taco": "7.5"}}), breaks)["source"] == "customer"
    for bad in ([{"min_qty": 1, "price": 1}], [{"min_qty": 5, "price": -1}]):
        with pytest.raises(ValueError):
            clean_breaks(bad)
    with pytest.raises(ValueError):
        clean_pricing({"discount_pct": 120})


def test_invoice_lines_take_the_customers_prices(h):
    h.seed("items", "taco", {"tenant_id": "hft", "name": "Tacos", "unit": "box", "kind": "finished", "price": 10})
    vip = call(h, action="SAVE_CUSTOMER", name="Big Events", pricing={"discount_pct": 10, "prices": {}}).fields["customer_id"]
    walk = call(h, action="SAVE_CUSTOMER", name="Walk-in").fields["customer_id"]
    assert call(h, action="SET_PRICE_BREAKS", item_id="taco", breaks=[{"min_qty": 100, "price": 8}]).ok
    assert call(h, action="SET_PRICE_BREAKS", item_id="nope", breaks=[]).reason == "UNKNOWN_ITEM"
    lines = [{"item_id": "taco", "qty": 120}, {"description": "Delivery to Marina", "qty": 1, "unit_price": "50", "charge": "delivery"},
             {"item_id": "taco", "qty": 2, "unit_price": "12"}]
    inv = call(h, action="SAVE_INVOICE", customer_id=vip, lines=lines).fields["invoice"]
    assert [(l["unit_price"], l.get("discount"), l.get("price_source")) for l in inv["lines"]] == [(800, "10", "break"), (5000, "0", None), (1200, "0", None)]
    assert inv["charges"] == 5000 and inv["subtotal"] == 120 * 720 + 5000 + 2400
    assert call(h, action="SAVE_INVOICE", customer_id=walk, lines=[{"description": "x", "qty": 1, "unit_price": 1, "charge": "tips"}]).reason == "INVALID_CHARGE"
    got = call(h, action="PRICE", item_id="taco", customer_id=walk, qty=3).fields
    assert (got["unit_price"], got["discount"], got["source"]) == ("10", "0", "list")
    pl = call(h, action="PRICE_LIST").fields
    assert pl["items"][0]["breaks"][0]["price"] == "8" and pl["discounts"][0]["name"] == "Big Events"
