# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""What valid items, suppliers and recipes look like (COS-01, ORD-01, KIT-01, KIT-02)."""
from __future__ import annotations

from dto import ItemKind

KINDS = {k.value for k in ItemKind}


def _name(value, low: int = 1) -> str:
    name = " ".join(str(value or "").split())
    if not low <= len(name) <= 80:
        raise ValueError("INVALID_NAME")
    return name


def quantity(value, reason: str = "INVALID_QUANTITY", allow_zero: bool = False) -> float:
    try:
        number = round(float(value), 4)
    except (TypeError, ValueError):
        raise ValueError(reason)
    if number < 0 or (number == 0 and not allow_zero) or number > 1_000_000:
        raise ValueError(reason)
    return int(number) if number.is_integer() else number


def clean_item(raw: dict, current: dict | None = None) -> dict:
    merged = {**(current or {}), **{k: v for k, v in raw.items() if v is not None}}
    kind = str(merged.get("kind") or "").lower()
    if kind not in KINDS:
        raise ValueError("INVALID_KIND")
    unit = " ".join(str(merged.get("unit") or "").split())
    if not 1 <= len(unit) <= 20:
        raise ValueError("INVALID_UNIT")
    return {"name": _name(merged.get("name")), "kind": kind, "unit": unit,
            "cost": quantity(merged.get("cost", 0), "INVALID_COST", allow_zero=True),
            "supplier_id": str(merged.get("supplier_id") or ""), "active": bool(merged.get("active", True)),
            "category": " ".join(str(merged.get("category") or "").split())[:40],
            "shelf_life_days": _days(merged.get("shelf_life_days")),           # warehouse-service dates new lots with it
            "barcode": "".join(str(merged.get("barcode") or "").split())[:40],   # scanned on the warehouse screens
            **({"sort": merged["sort"]} if isinstance(merged.get("sort"), int) else {})}   # listing order (REORDER)


def _days(value) -> int | None:
    if value in (None, ""):
        return None
    try:
        days = int(float(value))
    except (TypeError, ValueError):
        raise ValueError("INVALID_SHELF_LIFE")
    if not 0 < days <= 3650:
        raise ValueError("INVALID_SHELF_LIFE")
    return days


def clean_supplier(raw: dict, current: dict | None = None) -> dict:
    merged = {**(current or {}), **{k: v for k, v in raw.items() if v is not None}}
    phone = "".join(c for c in str(merged.get("phone") or "") if c.isdigit() or c == "+")[:20]
    return {"name": _name(merged.get("name"), 2), "phone": phone, "email": str(merged.get("email") or "").strip()[:120],
            "contact": " ".join(str(merged.get("contact") or "").split())[:80], "notes": str(merged.get("notes") or "")[:500],
            "active": bool(merged.get("active", True))}


def clean_recipe(raw: dict) -> dict:
    """KIT-02: output of one batch, and optionally what one batch uses (the MVP does not compare use with it - F3)."""
    lines = []
    for line in raw.get("ingredients") or []:
        lines.append({"item_id": str(line.get("item_id") or ""), "qty": quantity(line.get("qty"))})
    if any(not line["item_id"] for line in lines):
        raise ValueError("UNKNOWN_ITEM")
    return {"batch_output": quantity(raw.get("batch_output")), "ingredients": lines}
