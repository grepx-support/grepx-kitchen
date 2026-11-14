# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Each working document as data for ReportPdf: pure functions from what the screens already show to a spec
(title, facts, sections of tables or text, signature lines)."""
from __future__ import annotations

import base64
import binascii


def num(v, places: int = 2) -> str:
    if v in (None, ""):
        return "-"
    v = float(v)
    return f"{v:,.{places}f}".rstrip("0").rstrip(".") if places else f"{v:,.0f}"


def cash(cents, cur: str = "") -> str:
    return "-" if cents is None else f"{cur} {cents / 100:,.2f}".strip()


def closing(c: dict, place: str, cur: str) -> dict:
    """The day's closing in full: counts against the system with the difference and its value, sales by type, issues."""
    counts, value = [], 0.0
    for l in c.get("counts") or []:
        diff = float(l.get("difference") or 0)
        worth = diff * float(l.get("cost") or 0)
        value += worth
        counts.append({"cells": [l.get("item_name", ""), l.get("unit", ""), num(l.get("expected")), num(l.get("qty")), num(diff), num(worth)],
                       "flag": "bad" if diff < 0 else None})
    sales = [[k.replace("_", " ").capitalize(), num(v)] for k, v in (c.get("sales") or {}).items()] if isinstance(c.get("sales"), dict) else         [[s.get("type", ""), num(s.get("amount"))] for s in c.get("sales") or []]
    raw_issues = c.get("issues") or []
    issues = [[i.get("kind", ""), i.get("item_name", "") or i.get("item_id", ""), num(i.get("qty")), i.get("note", "")] for i in raw_issues] \
        if isinstance(raw_issues, list) else []
    return {"title": "Closing report", "subtitle": f"{place} - {c.get('date', '')}",
            "facts": [("Place", place), ("Day", c.get("date", "")), ("Counted by", c.get("staff_name") or c.get("user_name") or ""),
                      ("Submitted", (c.get("submitted_at") or "")[:16].replace("T", " ")), ("Items counted", str(len(counts))), ("Short items", str(sum(1 for r in counts if r["flag"]))),
                      ("Value of differences", f"{cur} {value:,.2f}"), ("Total sales", f"{cur} {sum(float(s[1].replace(',', '')) for s in sales if s[1] != '-'):,.2f}")],
            "sections": [{"heading": "Counts against the system", "columns": [("Item", 5, "L"), ("Unit", 1.4, "L"), ("System", 1.6, "R"), ("Counted", 1.6, "R"),
                                                                            ("Difference", 1.7, "R"), ("Value", 1.8, "R")], "rows": counts},
                         {"heading": "Sales", "columns": [("Type", 4, "L"), ("Amount", 2, "R")], "rows": sales, "empty": "No sales entered"},
                         {"heading": "Issues (waste, damage, staff meals...)", "columns": [("What", 2, "L"), ("Item", 3, "L"), ("Qty", 1, "R"), ("Note", 4, "L")],
                          "rows": issues, "empty": "No issues"} if isinstance(raw_issues, list) else {"heading": "Issues", "text": raw_issues},
                         {"heading": "Notes", "text": c.get("note") or c.get("notes") or ""}],
            "signatures": ["Counted by", "Checked by (manager)"]}


def payslip(s: dict, business: dict, cur: str) -> dict:
    lines = lambda xs: [[l["label"], cash(round(l["amount"] * 100), cur)] for l in xs]  # noqa: E731
    return {"title": "Payslip", "subtitle": f"{s['month']} - {s['name']}",
            "facts": [("Employee", s["name"]), ("Position", s.get("position", "")), ("Month", s["month"]), ("Hours worked", num(s.get("worked_hours"), 1)),
                      ("Gross", cash(round(s["gross"] * 100), cur)), ("Deductions", cash(round(sum(l["amount"] for l in s["deductions"]) * 100), cur)),
                      ("Net pay", cash(round(s["net"] * 100), cur)), ("Unpaid days", num(s.get("unpaid_days"), 1))],
            "sections": [{"heading": "Earnings", "columns": [("", 5, "L"), ("Amount", 2, "R")], "rows": lines(s["earnings"]), "total": ["Gross", cash(round(s["gross"] * 100), cur)]},
                         {"heading": "Deductions", "columns": [("", 5, "L"), ("Amount", 2, "R")], "rows": lines(s["deductions"]), "empty": "None"},
                         {"heading": "Paid by the employer on top", "columns": [("", 5, "L"), ("Amount", 2, "R")], "rows": lines(s["employer"]), "empty": "None"},
                         {"heading": "Net pay", "text": f"{cash(round(s['net'] * 100), cur)} - paid to the employee's account."}]}


def purchase_order(o: dict, business: dict) -> dict:
    sup = o.get("supplier") or {}
    rows = [[l.get("name", ""), l.get("unit", ""), num(l.get("qty") or l.get("ordered"))] for l in o.get("line_view") or o.get("lines") or []]
    return {"title": "Purchase order", "subtitle": f"{o.get('number', '')} - {sup.get('name', '')}",
            "facts": [("Order", o.get("number", "")), ("Supplier", sup.get("name", "")), ("Deliver to", o.get("location_name", "")),
                      ("Wanted by", o.get("delivery_date") or o.get("wanted_by") or "-"), ("Contact", sup.get("contact", "")), ("Phone", sup.get("phone", "")),
                      ("Email", sup.get("email", "")), ("Lines", str(len(rows)))],
            "sections": [{"heading": "Please supply", "columns": [("Item", 6, "L"), ("Unit", 1.5, "L"), ("Qty", 1.5, "R")], "rows": rows},
                         {"heading": "Note", "text": o.get("note") or "Please confirm the delivery date. Thank you."}],
            "signatures": ["Ordered by", "Received by"]}


def pick_list(p: dict) -> dict:
    rows = []
    for l in p.get("lines") or []:
        lots = l.get("lots") or [{}]
        for n, lot in enumerate(lots):
            rows.append([lot.get("bin_code", "-"), l.get("name", "") if n == 0 else "", num(lot.get("qty") if lot else l.get("qty")),
                         lot.get("expires_on", "") or "", "[  ]"])
    return {"title": "Pick list", "subtitle": f"{p.get('from_name', '')} to {p.get('to_name', '')}",
            "facts": [("From", p.get("from_name", "")), ("To", p.get("to_name", "")), ("Lines", str(len(p.get("lines") or []))), ("State", p.get("state", ""))],
            "sections": [{"heading": "Walk the bins in this order", "columns": [("Bin", 1.2, "L"), ("Item", 4, "L"), ("Qty", 1.2, "R"), ("Expires", 1.6, "L"),
                                                                              ("Picked", 1, "C")], "rows": rows}],
            "signatures": ["Picked by", "Checked by", "Received by"]}


def count_sheet(place: str, levels: list[dict], blind: bool = True) -> dict:
    rows = [[l.get("item_name") or l.get("name", ""), l.get("unit", ""), "" if blind else num(l.get("qty")), "", ""] for l in levels]
    return {"title": "Stock count sheet", "subtitle": place,
            "facts": [("Place", place), ("Items", str(len(rows))), ("Date", "____________"), ("Counted by", "____________")],
            "sections": [{"heading": "Count every item (write what you see, not what the system says)",
                          "columns": [("Item", 5, "L"), ("Unit", 1.3, "L"), ("System", 1.4, "R"), ("Counted", 1.6, "R"), ("Note", 3, "L")], "rows": rows}],
            "signatures": ["Counted by", "Checked by"]}


def safety_log(h: dict, places: dict, first: str, last: str, place: str) -> dict:
    rows = [{"cells": [r["at"].replace("T", " "), places.get(r.get("site_id"), ""), r.get("point_name", ""),
                       f"{num(r['value'], 1)}{r.get('unit', '')}" if r.get("value") is not None else ("; ".join(r.get("failed") or []) or "all yes"),
                       "yes" if r["ok"] else "NO", r.get("action_taken", ""), r.get("by", "")], "flag": None if r["ok"] else "bad"} for r in h["records"]]
    return {"title": "Food safety log", "subtitle": f"{place} - {first} to {last}", "orientation": "L",
            "facts": [("Place", place), ("From", first), ("To", last), ("Records", str(h["total"])), ("Out of range", str(h["failed"])),
                      ("In range", f"{round((1 - h['failed'] / h['total']) * 100) if h['total'] else 100}%")],
            "sections": [{"heading": "Every record", "columns": [("When", 1.6, "L"), ("Place", 2, "L"), ("Check", 2.6, "L"), ("Reading", 1.5, "R"), ("In range", 1, "C"),
                                                                ("Action taken", 3.4, "L"), ("By", 1.6, "L")], "rows": rows}],
            "signatures": ["Manager", "Inspector"]}


def picture(data_url: str) -> bytes | None:
    """A signature drawn on a phone (a PNG / JPEG data URL) as bytes; None when there is none or it is not one."""
    head, _, body = str(data_url or "").partition(",")
    if not head.startswith("data:image/") or ";base64" not in head:
        return None
    try:
        return base64.b64decode(body, validate=True)
    except (binascii.Error, ValueError):
        return None


def delivery_note(trip: dict, stop: dict | None, run: dict | None) -> dict:
    """What left the warehouse for one place, and - once handed over - who received it, when, and both signatures."""
    stop, run = stop or {}, run or {}
    rows = [[l.get("item_name", ""), l.get("unit", ""), num(l.get("qty"))] for l in trip.get("lines") or []]
    done = stop.get("state") == "delivered" or trip.get("state") == "delivered"
    at = (stop.get("delivered_at") or trip.get("delivered_at") or "")[:16].replace("T", " ")
    proof = (f"Received by {stop['receiver']} on {at}." if stop.get("receiver") else f"Marked delivered by {trip.get('delivered_by') or '-'} on {at}."
             ) if done else "Not delivered yet - to be signed on arrival."
    return {"title": "Delivery note", "subtitle": f"{trip.get('from', '')} to {trip.get('to', '')} - {trip.get('date', '')}",
            "facts": [("Note no.", str(trip.get("id", ""))[-8:].upper()), ("Date", trip.get("date", "")), ("From", trip.get("from", "")), ("To", trip.get("to", "")),
                      ("Driver", stop.get("driver") or run.get("driver_name") or "-"), ("Vehicle", run.get("vehicle") or "-"),
                      ("Sent by", trip.get("by", "")), ("Lines", str(len(rows)))],
            "sections": [{"heading": "Deliver to", "text": "\n".join(filter(None, [trip.get("to", ""), trip.get("to_address", "")]))},
                         {"heading": "Goods", "columns": [("Item", 6, "L"), ("Unit", 1.5, "L"), ("Qty", 1.5, "R")], "rows": rows},
                         {"heading": "Proof of delivery", "text": proof + (f"\nNote: {stop['note']}" if stop.get("note") else "")}],
            "signatures": [{"label": f"Driver - {stop.get('driver') or run.get('driver_name') or ''}".rstrip(" -"), "image": picture(stop.get("driver_signature"))},
                           {"label": f"Received by - {stop.get('receiver', '')}".rstrip(" -"), "image": picture(stop.get("signature"))}]}


KIND_WORDS = {"commit": "Promised", "receive": "Paid in", "return": "Paid back to you", "interest": "Interest"}


def investor_statement(st: dict) -> dict:
    """One party's statement: per fund promised, paid in, paid back, still promised and their share; then every movement
    of theirs in the period, with the original amount when it was paid in another currency."""
    def amt(cents: int, cur: str) -> str:
        return f"{cur} {cents / 100:,.2f}".strip()
    summary = [[f["name"], amt(f["committed"], f["currency"]), amt(f["received"], f["currency"]), amt(f["returned"], f["currency"]),
                amt(f["pending"], f["currency"]), f"{f['share_pct']}%"] for f in st["funds"]]
    lines = [[l["date"], f["name"], KIND_WORDS.get(l["kind"], l["kind"]), amt(l["amount"], f["currency"]),
              (f"{amt(l['original']['amount'], l['original']['currency'])} at {l['original']['rate']}" if l.get("original") else "") + (f" {l['ref']}" if l.get("ref") else "")]
             for f in st["funds"] for l in f["lines"]]
    period = f"{st['first']} to {st['last']}" if st["first"] > "0000-01-01" else f"to {st['last']}"
    return {"title": "Investor statement", "subtitle": f"{st['name']} - {period}",
            "facts": [("For", st["name"]), ("Period", period), ("Funds", str(len(st["funds"])))],
            "sections": [{"heading": "Your position", "columns": [("Fund", 4, "L"), ("Promised", 2.2, "R"), ("Paid in", 2.2, "R"), ("Paid back", 2.2, "R"),
                                                                    ("Still promised", 2.2, "R"), ("Share", 1.2, "R")], "rows": summary},
                         {"heading": "Movements", "columns": [("Date", 2, "L"), ("Fund", 3, "L"), ("What", 2.5, "L"), ("Amount", 2.5, "R"), ("Note", 4, "L")],
                          "rows": lines or [["", "", "No movements in this period", "", ""]]},
                         {"heading": "", "text": "Share is your part of the money paid into each fund. Amounts paid in another currency are shown at the rate they were converted."}]}
