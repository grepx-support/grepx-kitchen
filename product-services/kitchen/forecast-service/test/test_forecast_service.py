# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""forecast-service: demand from stock movements, the methods, picking the most accurate, kept forecasts."""
from datetime import date, timedelta
from pathlib import Path

import pytest
from grepx_config import load_config
from grepx_testkit.harness import ServiceHarness

from domain import METHODS, backtest, best, daily_demand, days_ahead, forecast_one, kept_accuracy, series, wape
from routes import handle

cfg = load_config(Path(__file__).resolve().parents[1] / "config")
T = "forecast_requests"
FRIDAY = 4


def weekly(end: date, n: int = 28) -> list[tuple[date, float]]:
    """n days up to end: 20 on Fridays, 10 on other days."""
    return [(end - timedelta(days=n - 1 - i), 20.0 if (end - timedelta(days=n - 1 - i)).weekday() == FRIDAY else 10.0) for i in range(n)]


# ---------------- rules ----------------
def test_demand_is_counted_sales_of_products_only():
    moves = [{"kind": "count", "qty": -5, "item_id": "taco", "location_id": "bondi", "date": "2026-11-01"},
             {"kind": "sale", "qty": -2, "item_id": "taco", "location_id": "bondi", "date": "2026-11-01"},
             {"kind": "waste", "qty": -9, "item_id": "taco", "location_id": "bondi", "date": "2026-11-01"},
             {"kind": "count", "qty": 3, "item_id": "taco", "location_id": "bondi", "date": "2026-11-02"},     # counted more: not demand
             {"kind": "count", "qty": -4, "item_id": "flour", "location_id": "bondi", "date": "2026-11-01"}]
    assert daily_demand(moves, {"taco"}) == {("bondi", "taco"): {"2026-11-01": 7.0}}
    s = series({"2026-11-01": 7.0, "2026-11-03": 1.0}, date(2026, 11, 4), 30)
    assert [q for _, q in s] == [7.0, 0.0, 1.0, 0.0] and series({}, date(2026, 11, 4), 30) == []


def test_methods_and_picking_the_most_accurate():
    end = date(2026, 11, 12)
    history, friday = weekly(end), date(2026, 11, 13)
    assert friday.weekday() == FRIDAY
    assert METHODS["weekday"].predict(history, [friday, friday + timedelta(days=1)]) == [20.0, 10.0]
    assert round(METHODS["moving_average"].predict(history, [friday])[0], 2) == round((20 + 60) / 7, 2)
    assert backtest(history, METHODS["weekday"]) == 0.0 and backtest(history[:10], METHODS["weekday"]) is None
    key, scores = best(history)
    assert key == "weekday" and scores["moving_average"] > 0
    growing = [(end - timedelta(days=27 - i), float(i)) for i in range(28)]
    assert METHODS["trend"].predict(growing, [end + timedelta(days=1)])[0] > 26
    assert wape([10, 10], [12, 8]) == 20.0 and wape([0], [3]) is None


def test_forecast_one_and_days():
    days = days_ahead("", date(2026, 11, 12))
    assert len(days) == 7 and days[0] == date(2026, 11, 13)
    got = forecast_one(weekly(date(2026, 11, 12)), days)
    assert got["method"] == "weekday" and got["forecast"][0] == {"date": "2026-11-13", "qty": 20.0} and got["total"] == 80.0
    assert forecast_one(weekly(date(2026, 11, 12)), days, "moving_average")["method"] == "moving_average"
    assert forecast_one([], days)["total"] == 0
    for bad in ("0", "29", "x"):
        with pytest.raises(ValueError, match="INVALID_DAYS"):
            days_ahead(bad, date(2026, 11, 12))
    with pytest.raises(ValueError, match="UNKNOWN_METHOD"):
        forecast_one([], days, "crystal_ball")


def test_kept_forecasts_are_checked_against_what_sold():
    kept = [{"date": "2026-11-10", "lines": [{"location_id": "bondi", "item_id": "taco", "qty": 12}]},
            {"date": "2026-11-12", "lines": [{"location_id": "bondi", "item_id": "taco", "qty": 9}]}]
    got = kept_accuracy(kept, {("bondi", "taco"): {"2026-11-10": 10.0}}, "2026-11-12")
    assert got == [{"date": "2026-11-10", "forecast": 12, "actual": 10.0, "error": 20.0}]


# ---------------- the service ----------------
@pytest.fixture()
def h():
    harness = ServiceHarness().add(cfg, T, handle, cfg.live_criteria)
    harness.seed("businesses", "hft", {"business_id": "hft", "tenant_id": "hft", "timezone": "UTC", "name": "HFT"})
    harness.seed("locations", "bondi", {"tenant_id": "hft", "name": "Bondi store", "kind": "store"})
    harness.seed("items", "taco", {"tenant_id": "hft", "name": "Tacos", "unit": "box", "kind": "finished"})
    harness.seed("items", "flour", {"tenant_id": "hft", "name": "Flour", "unit": "kg", "kind": "ingredient"})
    today = date.today()
    for d, q in weekly(today - timedelta(days=1)):
        harness.seed("stock_movements", f"m{d}", {"tenant_id": "hft", "kind": "count", "qty": -q, "item_id": "taco", "location_id": "bondi", "date": d.isoformat()})
    return harness


def call(h, **fields):
    return h.call(T, "forecast-service", {"actor_id": "u1", "actor_name": "Olivia", "tenant_id": "hft", **fields})


def test_forecast_action(h):
    got = call(h, action="FORECAST", days=7).fields
    row = got["rows"][0]
    assert (row["name"], row["location_name"], row["method"], row["error"]) == ("Tacos", "Bondi store", "weekday", 0.0)
    assert len(row["history"]) == 28 and got["products"][0]["total"] == 80.0 and len(got["methods"]) == 3
    assert call(h, action="FORECAST", days=40).reason == "INVALID_DAYS"
    assert call(h, action="FORECAST", location_id="mars").reason == "UNKNOWN_LOCATION"
    assert call(h, action="FORECAST", tenant_id="ghost").reason == "UNKNOWN_BUSINESS"


def test_snapshot_keeps_each_day_once(h):
    first = call(h, action="SNAPSHOT").fields["kept"]
    assert first == [date.today().isoformat(), (date.today() + timedelta(days=1)).isoformat()]
    assert call(h, action="SNAPSHOT").fields["kept"] == []
