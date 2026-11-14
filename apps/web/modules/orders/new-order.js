/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// A purchase order from scratch: choose the supplier, drag in the items.
import { api, run, toast } from "/assets/app.js";
import { Builder, html } from "/assets/kit/index.js";
import { biz } from "../lib/business.js";
import { catalogue, notFinished } from "../lib/items.js";
import { frame } from "./common.js";

export async function newOrder(el) {
  const body = frame(el, "new", "Pick the supplier, then drag items into the order.");
  const b = await biz();
  const place = b.locations.find((l) => l.holding);
  const [sup, items] = await Promise.all([api("/orders/suppliers"), catalogue(notFinished)]);
  if (!place || !sup.suppliers.length) { body.innerHTML = '<div class="card"><p>Set up a holding place and at least one supplier first (Setup).</p></div>'; return; }
  body.innerHTML = String(html`<div class="card accent"><div class="k-bar"><label class="grow">Supplier<select name="supplier">${sup.suppliers.map((s) =>
    html`<option value="${s.id}">${s.name}</option>`)}</select></label><button class="btn primary" data-save>Save purchase order</button></div><div class="slot"></div></div>`);
  const builder = new Builder({ items, title: "Items", label: "Order" });
  builder.mount(body.querySelector(".slot"));
  body.querySelector("[data-save]").onclick = async () => {
    const lines = builder.lines();
    if (!lines.length) return toast("Add at least one line.");
    const po = await run(() => api("/orders", { method: "POST", body: { supplier_id: body.querySelector("select").value, location_id: place.id, lines } }), "Purchase order saved");
    if (po) location.hash = `#/orders/${po.po_id}`;
  };
}
