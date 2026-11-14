# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""SEND - send an open order to its supplier on the chosen channels (email to the supplier's email, WhatsApp / SMS to
their phone), with the order's PDF attached when the caller made one (attachments=[{name, mime, data_b64, url}]).
notification-service sends it - or only logs it until the business connects a provider."""
import grepx_contracts as gc
from grepx_service import RequestContext, notify, now_iso

from dto import ReasonCode, Table
from .common import Stop, business, order, own, run

CHANNELS = ("email", "whatsapp", "sms")


def handle(ctx: RequestContext) -> None:
    def body():
        biz = business(ctx)
        po = {k: v for k, v in order(ctx, biz["_key"]).items() if not k.startswith("_")}
        supplier = own(ctx, gc.item.SUPPLIERS, po["supplier_id"], biz["_key"], ReasonCode.UNKNOWN_SUPPLIER)
        channels = [c for c in ctx.get("channels") or ["email", "whatsapp"]]
        if not channels or any(c not in CHANNELS for c in channels):
            raise Stop(ReasonCode.INVALID_CHANNEL)
        sent = notify(ctx.emitter, "purchase_order", email=supplier.get("email", ""), phone=supplier.get("phone", ""), channels=channels,
                      ref=f"po-{po['po_id']}-{len(po.get('sent') or [])}", tenant_id=biz["_key"], auto=False,
                      attachments=[a for a in ctx.get("attachments") or [] if isinstance(a, dict)] or None,
                      values={"org": biz.get("name", ""), "supplier": supplier.get("name", ""), "number": po.get("number", ""),
                              "text": po.get("text", "")})
        if not sent:
            raise Stop(ReasonCode.NO_CONTACT)
        po["sent"] = [*(po.get("sent") or []), {"at": now_iso(), "channels": channels, "by": ctx.text("actor_name")}]
        ctx.emitter.submit(Table.PURCHASE_ORDERS.value, po["po_id"], "ACCEPTED", po)
        return po
    run(ctx, body)
