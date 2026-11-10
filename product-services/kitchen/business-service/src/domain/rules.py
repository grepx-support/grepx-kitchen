# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""What a valid business and location look like.

Business = one tenant. Settings drive planning and costing (R4, R5, R9, ORD-04): how many past weeks feed targets,
the safety buffer, what counts as a large change between recommendations, the acceptable COGS range, the sales types
staff enter at closing (Q8). Locations: a holding place keeps stock for everyone (D1); one place may be both a kitchen
and the holding place (D2, BUS-04); only kitchens make finished goods (D6).
"""
from __future__ import annotations

import re
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from dto import LocationKind, Module

DEFAULT_SETTINGS = {
    "target_weeks": 2,          # R5 / KIT-03: past weeks used for targets and recommendations (1-3)
    "safety_pct": 10,           # R5: buffer added to production targets and reorder quantities
    "large_change_pct": 30,     # ORD-04: a recommendation this much above or below the last one is flagged
    "cogs_min": 25,             # R9 / COS-07: acceptable COGS range, % of sales
    "cogs_max": 35,
    "sales_types": ["Sales", "Other sales"],   # Q8: what staff enter at closing
}
LIMITS = {"target_weeks": (1, 3), "safety_pct": (0, 200), "large_change_pct": (1, 1000), "cogs_min": (0, 100), "cogs_max": (0, 100)}
KINDS = {k.value for k in LocationKind}
MODULES = [m.value for m in Module]


def _name(value) -> str:
    name = " ".join(str(value or "").split())
    if not 2 <= len(name) <= 80:
        raise ValueError("INVALID_NAME")
    return name


def clean_settings(raw: dict, current: dict) -> dict:
    out = {**DEFAULT_SETTINGS, **(current or {})}
    for key, value in (raw or {}).items():
        if key in LIMITS:
            low, high = LIMITS[key]
            try:
                number = float(value)
            except (TypeError, ValueError):
                raise ValueError("INVALID_SETTING")
            if not low <= number <= high:
                raise ValueError("INVALID_SETTING")
            out[key] = int(number) if number.is_integer() else number
        elif key == "sales_types":
            types = [" ".join(str(t).split()) for t in (value or []) if str(t).strip()]
            if not types or len(types) > 10:
                raise ValueError("INVALID_SETTING")
            out[key] = list(dict.fromkeys(types))
    if out["cogs_min"] > out["cogs_max"]:
        raise ValueError("INVALID_SETTING")
    return out


def clean_business(raw: dict, current: dict | None = None) -> dict:
    """The business row from a request (CREATE: everything; UPDATE: only what was sent changes)."""
    cur = dict(current or {})
    out = {"name": _name(raw["name"]) if "name" in raw or not cur else cur["name"]}
    currency = str(raw.get("currency", cur.get("currency", "")) or "").upper().strip()
    if not re.fullmatch(r"[A-Z]{3}", currency):
        raise ValueError("INVALID_CURRENCY")
    timezone = str(raw.get("timezone", cur.get("timezone", "")) or "").strip()
    try:
        ZoneInfo(timezone)
    except (ZoneInfoNotFoundError, ValueError):
        raise ValueError("INVALID_TIMEZONE")
    modules = dict(cur.get("modules") or {m: True for m in MODULES})       # BUS-03: all on until switched off
    for key, value in (raw.get("modules") or {}).items():
        if key in MODULES:
            modules[key] = bool(value)
    out.update({"currency": currency, "timezone": timezone, "modules": modules,
                "settings": clean_settings(raw.get("settings") or {}, cur.get("settings") or {})})
    return out


def clean_location(raw: dict, current: dict | None = None) -> dict:
    cur = dict(current or {})
    merged = {**cur, **{k: v for k, v in raw.items() if v is not None}}
    kind = str(merged.get("kind") or "").lower()
    if kind not in KINDS:
        raise ValueError("INVALID_KIND")
    holding = bool(merged.get("holding", kind == LocationKind.WAREHOUSE.value))
    try:
        cover = int(merged.get("days_of_cover", 3))
        every = int(merged.get("count_every_days", 1))
    except (TypeError, ValueError):
        raise ValueError("INVALID_SETTING")
    if not 1 <= cover <= 60 or every not in (1, 3, 7):          # R4 / R10
        raise ValueError("INVALID_SETTING")
    return {"name": _name(merged.get("name")), "kind": kind, "holding": holding, "makes_goods": kind == LocationKind.KITCHEN.value,
            "days_of_cover": cover, "count_every_days": every, "active": bool(merged.get("active", True)),
            "address": " ".join(str(merged.get("address") or "").split())[:200],
            **({"sort": merged["sort"]} if isinstance(merged.get("sort"), int) else {})}   # listing order (REORDER_LOCATIONS)


def holding_left(locations: list[dict], changed_id: str, changed: dict) -> bool:
    """D1: once a business has locations, at least one active one must hold stock for the others."""
    after = {r.get("location_id") or r.get("_key"): r for r in locations}
    after[changed_id] = changed
    active = [r for r in after.values() if r.get("active", True)]
    return not active or any(r.get("holding") for r in active)
