# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Working documents as PDF, each with the business letterhead and logo (documents/report.py, specs.py): the closing
report, a payslip, a purchase order, a delivery note (with the driver's and the receiver's signatures), a pick list, a
stock count sheet and the food safety log. Each one reuses the data
its screen already shows and the same permission. The *_file builders are also used to attach a document to a message
(routers/dispatch.py)."""
import grepx_contracts as gc
from fastapi import APIRouter, Depends
from grepx_bff.errors import ApiError

from documents import PdfFile, ReportPdf, brand, specs
from kitchen import Kitchen, allow
from . import closing, orders, payroll, safety, stock, warehouse

router = APIRouter(prefix="/pdf", tags=["pdf"])


def report(spec: dict, k: Kitchen, name: str) -> PdfFile:
    return PdfFile(ReportPdf(spec, brand(k)).build(), name)


def payslip_file(month: str, employee_id: str, k: Kitchen) -> PdfFile:
    slip = next((s for s in payroll.month(month=month, k=k)["payslips"] if s["employee_id"] == employee_id), None)
    if slip is None:
        raise ApiError("NOT_FOUND", 404)
    return report(specs.payslip(slip, k.business, k.business.get("currency", "")), k, f"payslip-{month}-{slip['name'].replace(' ', '-')}")


def order_file(po_id: str, k: Kitchen) -> PdfFile:
    o = orders.order(po_id=po_id, k=k)
    return report(specs.purchase_order(o, k.business), k, f"order-{o.get('number') or po_id}")


def delivery_note_file(delivery_id: str, k: Kitchen) -> PdfFile:
    trip = stock.trip(delivery_id, k)
    run = next((r for r in k.rows(gc.delivery.RUNS) for s in r.get("stops") or [] if s.get("delivery_id") == delivery_id
                and s.get("state") == "delivered"), None)
    stop = next((s for s in (run or {}).get("stops") or [] if s.get("delivery_id") == delivery_id), None)
    return report(specs.delivery_note(trip, stop, run), k, f"delivery-note-{trip['date']}-{trip['to'].replace(' ', '-')}")


@router.get("/delivery/{delivery_id}")
def delivery_note(delivery_id: str, k: Kitchen = Depends(allow("delivery", "warehouse_out", "manage_business", "view_stock"))):
    return delivery_note_file(delivery_id, k).response()


@router.get("/closing/{closing_id}")
def closing_report(closing_id: str, k: Kitchen = Depends(allow("manage_business", "view_costs", "closing"))):
    found = next((c for c in closing.history(k=k)["closings"] if c.get("closing_id") == closing_id), None)
    if found is None:
        raise ApiError("NOT_FOUND", 404)
    items = k.items()
    found["counts"] = [{**l, "cost": items.get(l["item_id"], {}).get("cost", 0)} for l in found["counts"]]
    return report(specs.closing(found, found.get("location_name", ""), k.business.get("currency", "")), k,
                  f"closing-{closing_id.split(':')[-1]}").response()


@router.get("/payslip")
def payslip(month: str, employee_id: str, k: Kitchen = Depends(allow("manage_business"))):
    return payslip_file(month, employee_id, k).response()


@router.get("/order/{po_id}")
def purchase_order(po_id: str, k: Kitchen = Depends(allow("orders", "warehouse_in"))):
    return order_file(po_id, k).response()


@router.get("/pick/{pick_id}")
def pick(pick_id: str, k: Kitchen = Depends(warehouse.PICKER)):
    return report(specs.pick_list(warehouse.pick_list(pick_id=pick_id, k=k)), k, f"pick-{pick_id}").response()


@router.get("/count-sheet")
def count_sheet(location_id: str, blind: bool = True, k: Kitchen = Depends(allow("adjust_stock", "manage_business", "closing", "view_stock"))):
    place = k.one(gc.business.LOCATIONS, location_id) or {}
    items = k.items()
    levels = sorted(({"item_name": items.get(l["item_id"], {}).get("name", ""), "unit": items.get(l["item_id"], {}).get("unit", ""), "qty": l.get("qty")}
                     for l in k.rows(gc.stock.STOCK_LEVELS, location_id=location_id) if items.get(l["item_id"], {}).get("active", True)),
                    key=lambda l: l["item_name"].lower())
    return report(specs.count_sheet(place.get("name", ""), levels, blind), k, f"count-sheet-{place.get('name', 'place').replace(' ', '-')}").response()


@router.get("/safety")
def safety_log(first: str, last: str, site_id: str = "", k: Kitchen = Depends(safety.manager)):
    h = safety.history(first=first, last=last, site_id=site_id, k=k)
    places = {r["_key"]: r.get("name", "") for r in k.rows(gc.business.LOCATIONS)}
    return report(specs.safety_log(h, places, first, last, places.get(site_id, "Every place")), k, f"food-safety-{first}-{last}").response()
