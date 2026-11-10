# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""A delivery run: its stops in order, arrival estimates, and which state may follow which.

ETA: the van leaves at the start time; each stop takes DRIVE minutes to reach and SERVICE minutes to unload (owner can
change both per run). Delivered or failed stops keep their real times; estimates move with what is left.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta

DRIVE, SERVICE = 25, 10
SIGNATURE_MAX = 60_000            # a PNG data URL of a finger signature is a few KB; this stops photos being stuffed in
OPEN_STOPS = ("pending", "arrived")
NEXT = {"pending": ("arrived", "delivered", "failed"), "arrived": ("delivered", "failed")}


def clean_run(raw: dict) -> dict:
    try:
        day = date.fromisoformat(str(raw.get("date") or "")).isoformat()
    except ValueError:
        raise ValueError("INVALID_DATE")
    start = str(raw.get("start_time") or "08:00")
    try:
        datetime.strptime(start, "%H:%M")
    except ValueError:
        raise ValueError("INVALID_TIME")
    name = " ".join(str(raw.get("name") or f"Run {day}").split())[:60]
    if len(name) < 2:
        raise ValueError("INVALID_NAME")
    return {"date": day, "start_time": start, "name": name, "vehicle": " ".join(str(raw.get("vehicle") or "").split())[:40],
            "driver_id": str(raw.get("driver_id") or ""), "driver_name": " ".join(str(raw.get("driver_name") or "").split())[:80],
            "drive_minutes": _minutes(raw.get("drive_minutes"), DRIVE), "service_minutes": _minutes(raw.get("service_minutes"), SERVICE)}


def _minutes(value, default: int) -> int:
    try:
        return max(1, min(240, int(value)))
    except (TypeError, ValueError):
        return default


def eta(run: dict, stops: list[dict], now: datetime | None = None) -> list[dict]:
    """Stops with "eta" (HH:MM): from now when the van is on the road, else from the run's start time."""
    if now and run.get("state") == "on_road":
        clock = now
    else:
        clock = datetime.combine(date.fromisoformat(run["date"]), datetime.strptime(run["start_time"], "%H:%M").time())
    out = []
    for stop in stops:
        if stop["state"] in OPEN_STOPS:
            clock += timedelta(minutes=run["drive_minutes"])
            out.append({**stop, "eta": clock.strftime("%H:%M")})
            clock += timedelta(minutes=run["service_minutes"])
        else:
            out.append(stop)
    return out


def may_move(stop: dict, to: str) -> bool:
    return to in NEXT.get(stop.get("state", ""), ())


def finished(stops: list[dict]) -> bool:
    return all(s["state"] not in OPEN_STOPS for s in stops)


def check_signature(signature: str) -> str:
    signature = str(signature or "")
    if signature and (not signature.startswith("data:image/") or len(signature) > SIGNATURE_MAX):
        raise ValueError("SIGNATURE_TOO_LARGE")
    return signature
