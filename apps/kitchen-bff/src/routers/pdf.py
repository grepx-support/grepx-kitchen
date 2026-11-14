# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Working documents as PDF, each with the business letterhead (documents/report.py, specs.py): the closing report,
a payslip, a purchase order, a pick list, a stock count sheet and the
food safety log. Each one reuses the data its screen already shows and the same permission."""
import grepx_contracts as gc
from fastapi import APIRouter, Depends
from fastapi.responses import Response
from grepx_bff.errors import ApiError

from documents import ReportPdf, specs
from kitchen import Kitchen, allow
from . import closing, orders, payroll, safety, warehouse

router = APIRouter(prefix="/pdf", tags=["pdf"])


def pdf(spec: dict, k: Kitchen, name: str) -> Response:
    data = ReportPdf(spec, k.business).build()
    return Response(data, media_type="application/pdf", headers={"Content-Disposition": f'inline; filename="{name}.pdf"'})


@router.get("/closing/{closing_id}")
def closing_report(closing_id: str, k: Kitchen = Depends(allow("manage_business", "view_costs", "closing"))):
    found = next((c for c in closing.history(k=k)["closings"] if c.get("closing_id") == closing_id), None)
    if found is None:
        raise ApiError("NOT_FOUND", 404)
    items = k.items()
    found["counts"] = [{**l, "cost": items.get(l["item_id"], {}).get("cost", 0)} for l in found["counts"]]
    return pdf(specs.closing(found, found.get("location_name", ""), k.business.get("currency", "")), k, f"closing-{closing_id.split(':')[-1]}")


@router.get("/payslip")
def payslip(month: str, employee_id: str, k: Kitchen = Depends(allow("manage_business"))):
    slip = next((s for s in payroll.month(month=month, k=k)["payslips"] if s["employee_id"] == employee_id), None)
    if slip is None:
        raise ApiError("NOT_FOUND", 404)
    return pdf(specs.payslip(slip, k.business, k.business.get("currency", "")), k, f"payslip-{month}-{slip['name'].replace(' ', '-')}")


@router.get("/order/{po_id}")
def purchase_order(po_id: str, k: Kitchen = Depends(allow("orders", "warehouse_in"))):
    o = orders.order(po_id=po_id, k=k)
    return pdf(specs.purchase_order(o, k.business), k, f"order-{o.get('number') or po_id}")


@router.get("/pick/{pick_id}")
def pick(pick_id: str, k: Kitchen = Depends(warehouse.PICKER)):
    return pdf(specs.pick_list(warehouse.pick_list(pick_id=pick_id, k=k)), k, f"pick-{pick_id}")


@router.get("/count-sheet")
def count_sheet(location_id: str, blind: bool = True, k: Kitchen = Depends(allow("adjust_stock", "manage_business", "closing", "view_stock"))):
    place = k.one(gc.business.LOCATIONS, location_id) or {}
    items = k.items()
    levels = sorted(({"item_name": items.get(l["item_id"], {}).get("name", ""), "unit": items.get(l["item_id"], {}).get("unit", ""), "qty": l.get("qty")}
                     for l in k.rows(gc.stock.STOCK_LEVELS, location_id=location_id) if items.get(l["item_id"], {}).get("active", True)),
                    key=lambda l: l["item_name"].lower())
    return pdf(specs.count_sheet(place.get("name", ""), levels, blind), k, f"count-sheet-{place.get('name', 'place').replace(' ', '-')}")


@router.get("/safety")
def safety_log(first: str, last: str, site_id: str = "", k: Kitchen = Depends(safety.manager)):
    h = safety.history(first=first, last=last, site_id=site_id, k=k)
    places = {r["_key"]: r.get("name", "") for r in k.rows(gc.business.LOCATIONS)}
    return pdf(specs.safety_log(h, places, first, last, places.get(site_id, "Every place")), k, f"food-safety-{first}-{last}")
