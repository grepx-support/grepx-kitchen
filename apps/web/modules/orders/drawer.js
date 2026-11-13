/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// One order in the side drawer: everything about it next to the board or list, with its quick actions.
import { api } from "/assets/app.js";
import { html, icon, openDrawer } from "/assets/kit/index.js";
import { orderSummary } from "./summary.js";

export async function showOrder(id, b, title = "Order") {
  const d = openDrawer({ title, body: '<div class="kit-skeleton" style="height:240px"></div>' });
  try {
    const o = await api(`/orders/${id}`);
    const wa = o.supplier?.phone ? `https://wa.me/${o.supplier.phone.replace(/\D/g, "")}?text=${encodeURIComponent(o.text || "")}` : "";
    d.el.querySelector("h2").textContent = `${o.number} · ${o.supplier?.name || o.supplier_name}`;
    d.body.innerHTML = String(html`<div class="o-actions"><a class="btn small primary" href="#/orders/${id}">${icon("arrow", { size: 14 })} Open the order page</a>
        ${wa ? html`<a class="btn small" target="_blank" rel="noopener" href="${wa}">${icon("message", { size: 14 })} WhatsApp the supplier</a>` : ""}
        ${o.supplier?.email ? html`<a class="btn small" href="mailto:${o.supplier.email}?subject=${encodeURIComponent(o.number)}">${icon("mail", { size: 14 })} Email</a>` : ""}</div>
      ${orderSummary(o, b)}`);
  } catch (e) {
    d.body.innerHTML = String(html`<p class="bad">Couldn't load: ${e.message}</p>`);
  }
}
