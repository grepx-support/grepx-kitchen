# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Monthly costs of a place as lines: a category (salaries, rent, electricity, delivery-app commission...), the group it
counts in - staff (labour), premises (rent) or running costs (other) - the amount, a note, and whether it is a share of
a cost the business pays once for several places. The three group totals keep feeding the daily costing (Q10)."""
from __future__ import annotations

import re
from decimal import ROUND_HALF_UP, Decimal

GROUPS = {"labour": "Staff", "rent": "Premises", "other": "Running costs"}
CATEGORIES = [("Salaries and wages", "labour"), ("Overtime and casual staff", "labour"), ("Staff meals", "labour"),
              ("Staff benefits (PF / CPF / super)", "labour"), ("Rent", "rent"), ("Service charge / maintenance", "rent"),
              ("Property tax", "rent"), ("Electricity", "other"), ("Gas", "other"), ("Water", "other"), ("Internet and phone", "other"),
              ("Delivery-app commission", "other"), ("Card / UPI fees", "other"), ("Marketing", "other"), ("Repairs and maintenance", "other"),
              ("Cleaning and pest control", "other"), ("Licences and permits", "other"), ("Insurance", "other"), ("Software and POS", "other"),
              ("Accounting and legal", "other"), ("Vehicle fuel", "other"), ("Other", "other")]
SPLITS = ("equal", "sales", "custom")
MONTH = re.compile(r"^20\d\d-(0[1-9]|1[0-2])$")


def money(value) -> float:
    try:
        v = Decimal(str(value if value not in (None, "") else 0))
    except Exception:
        raise ValueError("INVALID_AMOUNT")
    if v < 0 or v > Decimal("1e10"):
        raise ValueError("INVALID_AMOUNT")
    return float(v.quantize(Decimal("0.01"), ROUND_HALF_UP))


def clean_lines(raw) -> list[dict]:
    """Cost lines from a form: empty rows dropped, the same category twice summed into one."""
    out: dict[tuple, dict] = {}
    for r in raw or []:
        name = " ".join(str(r.get("category") or "").split())[:60]
        amount = money(r.get("amount"))
        if not name or (not amount and not r.get("keep")):
            continue
        group = r.get("group") or dict(CATEGORIES).get(name, "other")
        if group not in GROUPS:
            raise ValueError("INVALID_GROUP")
        key = (name, bool(r.get("shared")))
        line = out.setdefault(key, {"category": name, "group": group, "amount": 0.0, "note": "", **({"shared": True} if r.get("shared") else {})})
        line["amount"] = round(line["amount"] + amount, 2)
        line["note"] = (line["note"] or " ".join(str(r.get("note") or "").split()))[:120]
    return list(out.values())


def totals(lines: list[dict]) -> dict[str, float]:
    """labour / rent / other - what the daily costing spreads over the month."""
    out = {g: 0.0 for g in GROUPS}
    for l in lines:
        out[l["group"]] = round(out[l["group"]] + l["amount"], 2)
    return out


def legacy_lines(row: dict | None) -> list[dict]:
    """A month saved before lines existed: its three amounts as one line each."""
    if not row:
        return []
    if row.get("lines") is not None:
        return row["lines"]
    names = {"labour": "Salaries and wages", "rent": "Rent", "other": "Other"}
    return [{"category": names[g], "group": g, "amount": float(row[g]), "note": ""} for g in GROUPS if row.get(g)]


def split(amount: float, weights: dict[str, float]) -> dict[str, float]:
    """A shared cost over places by weight (equal: all 1). Cents add up exactly: the rounding goes to the last place."""
    total = sum(w for w in weights.values() if w > 0)
    if not weights or total <= 0:
        raise ValueError("NO_PLACES")
    ids = [k for k, w in weights.items() if w > 0]
    parts = {k: round(amount * weights[k] / total, 2) for k in ids}
    parts[ids[-1]] = round(amount - sum(parts[k] for k in ids[:-1]), 2)
    return parts


def with_share(lines: list[dict], category: str, group: str, amount: float, note: str) -> list[dict]:
    """The place's lines with its share of a shared cost set (an earlier share of the same category replaced)."""
    rest = [l for l in lines if not (l["category"] == category and l.get("shared"))]
    return rest + ([{"category": category, "group": group, "amount": amount, "note": note, "shared": True}] if amount else [])


def next_month(month: str) -> str:
    y, m = int(month[:4]), int(month[5:])
    return f"{y + m // 12}-{m % 12 + 1:02d}"


def breakdown(rows: list[dict], share: float = 1.0) -> list[dict]:
    """Cost lines of several places summed per category (largest first), scaled by `share` of the month."""
    out: dict[str, dict] = {}
    for row in rows:
        for l in legacy_lines(row):
            c = out.setdefault(l["category"], {"category": l["category"], "group": l["group"], "amount": 0.0})
            c["amount"] = round(c["amount"] + l["amount"] * share, 2)
    return sorted(out.values(), key=lambda c: -c["amount"])


def grid(rows: list[dict], places: dict[str, str], months: list[str]) -> list[dict]:
    """Month by month, place by place: the three group totals, the total, its change on the month before, the lines."""
    by = {(r["location_id"], r["month"]): r for r in rows}
    out = []
    for pid, name in places.items():
        before = None
        for month in months:
            r = by.get((pid, month))
            lines = legacy_lines(r)
            t = totals(lines) if r else {g: None for g in GROUPS}
            total = round(sum(t.values()), 2) if r else None
            change = round((total - before) * 100 / before, 1) if total is not None and before else None
            out.append({"location_id": pid, "location_name": name, "month": month, **t, "total": total, "change_pct": change, "lines": lines,
                        "shared": round(sum(l["amount"] for l in lines if l.get("shared")), 2)})
            before = total if total is not None else before
    return out
