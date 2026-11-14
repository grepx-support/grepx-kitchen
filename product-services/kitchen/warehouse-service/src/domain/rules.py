# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Bins and pick lines: what a valid bin and a valid line look like."""
from __future__ import annotations

ZONES = ("dry", "chilled", "frozen", "packaging")


def clean_bin(raw: dict) -> dict:
    code = " ".join(str(raw.get("code") or "").split()).upper()
    if not 1 <= len(code) <= 20:
        raise ValueError("INVALID_CODE")
    zone = str(raw.get("zone") or "dry").lower()
    if zone not in ZONES:
        raise ValueError("INVALID_ZONE")
    return {"code": code, "zone": zone, "note": str(raw.get("note") or "")[:120], "active": bool(raw.get("active", True))}


def clean_lines(lines) -> list[dict]:
    out = {}
    for line in lines or []:
        try:
            qty = float(line.get("qty"))
        except (TypeError, ValueError, AttributeError):
            raise ValueError("INVALID_QUANTITY")
        if qty <= 0:
            raise ValueError("INVALID_QUANTITY")
        key = str(line.get("item_id") or "")
        out[key] = round(out.get(key, 0) + qty, 4)
    if not out:
        raise ValueError("NO_LINES")
    return [{"item_id": k, "qty": q} for k, q in out.items()]
