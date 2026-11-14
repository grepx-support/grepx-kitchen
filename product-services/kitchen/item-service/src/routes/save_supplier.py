# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""SAVE_SUPPLIER - the business's list of suppliers (ORD-01)."""
from grepx_service import RequestContext, new_key

from domain import clean_supplier
from dto import ReasonCode, Table
from .common import guard, mine

FIELDS = ("name", "phone", "email", "contact", "notes", "active")


def handle(ctx: RequestContext) -> None:
    tenant = guard(ctx)
    if tenant is None:
        return
    supplier_id = ctx.text("supplier_id")
    current = mine(ctx, Table.SUPPLIERS.value, supplier_id, tenant)
    if supplier_id and current is None:
        return ctx.reject(ReasonCode.UNKNOWN_SUPPLIER)
    try:
        row = clean_supplier({k: ctx.get(k) for k in FIELDS if ctx.get(k) is not None}, current)
    except ValueError as exc:
        return ctx.reject(str(exc))
    supplier_id = supplier_id or new_key()[:12]
    full = {"supplier_id": supplier_id, "tenant_id": tenant, **row}
    ctx.emitter.submit(Table.SUPPLIERS.value, supplier_id, "ACCEPTED", full)
    ctx.accept({"supplier": full})
