# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Bulk import and export (Setup -> Import / export): a template to fill in, everything out as Excel or CSV, and a file
in - first checked row by row (nothing saved, every problem shown), then imported through the owning services."""
import base64
import binascii

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from grepx_bff.errors import ApiError
from grepx_bff.tabular import TableError, read, write_csv, write_xlsx

from imports import IMPORTERS
from kitchen import Kitchen, allow

router = APIRouter(prefix="/data", tags=["import-export"])
owner = allow("manage_business")
XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def importer(kind: str):
    if kind not in IMPORTERS:
        raise ApiError("NOT_FOUND", 404)
    return IMPORTERS[kind]


def file_out(name: str, headings: list[str], rows: list[list], fmt: str, notes: list[str]) -> Response:
    if fmt == "csv":
        return Response(write_csv(headings, rows), media_type="text/csv", headers={"Content-Disposition": f'attachment; filename="{name}.csv"'})
    return Response(write_xlsx(headings, rows, name[:31], notes), media_type=XLSX, headers={"Content-Disposition": f'attachment; filename="{name}.xlsx"'})


@router.get("")
def kinds(k: Kitchen = Depends(owner)):
    return {"kinds": [{"kind": i.kind, "title": i.title, "notes": list(i.notes),
                       "columns": [{"heading": c.heading, "required": c.required, "help": c.help or c.kind, "example": c.example} for c in i.columns]}
                      for i in IMPORTERS.values()]}


@router.get("/{kind}/template")
def template(kind: str, format: str = "xlsx", k: Kitchen = Depends(owner)):
    i = importer(kind)
    return file_out(f"{i.kind}-template", i.headings(), i.template(), format, i.help())


@router.get("/{kind}/export")
def export(kind: str, format: str = "xlsx", k: Kitchen = Depends(owner)):
    i = importer(kind)
    return file_out(f"{i.kind}-{k.business.get('name', 'export').replace(' ', '-')}", [c.heading for c in i.columns], i.export(k, i.context(k)), format, i.help())


def parse(body: dict):
    head, _, data = str(body.get("file") or "").partition(",")
    try:
        raw = base64.b64decode(data or head, validate=True)
    except (binascii.Error, ValueError):
        raise ApiError("NOT_A_SPREADSHEET", 400)
    try:
        return read(raw, str(body.get("name") or "upload.csv"))
    except TableError as exc:
        raise ApiError(str(exc), 400)


def report(plan, saved: bool) -> dict:
    rows = [{"rows": p.rows, "label": p.label, "action": p.action, "errors": p.errors} for p in plan]
    ok = [p for p in plan if not p.errors]
    return {"saved": saved, "total": len(plan), "ok": len(ok), "failed": len(plan) - len(ok),
            "creates": sum(p.action == "create" for p in ok), "updates": sum(p.action == "update" for p in ok), "rows": rows}


@router.post("/{kind}/check")
def check(kind: str, body: dict, k: Kitchen = Depends(owner)):
    """Every row checked, nothing saved."""
    i = importer(kind)
    return report(i.plan(parse(body).rows, i.context(k)), False)


@router.post("/{kind}/import")
def run_import(kind: str, body: dict, k: Kitchen = Depends(owner)):
    """Import the rows that pass; the ones that do not are listed with why (nothing half-saved: each row is one save)."""
    i = importer(kind)
    k.gw.limit(f"import:{k.tenant}", rate=20, per=600)
    return report(i.run(k, i.plan(parse(body).rows, i.context(k))), True)
