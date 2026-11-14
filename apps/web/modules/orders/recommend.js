/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// The reorder recommendation, one card per supplier: adjust by dragging items in or changing quantities, then save.
import { api, run, toast } from "/assets/app.js";
import { Builder, h, html, pill } from "/assets/kit/index.js";
import { biz } from "../lib/business.js";
import { fmt } from "../lib/format.js";
import { catalogue, notFinished } from "../lib/items.js";
import { frame } from "./common.js";

const hint = (l) => `use ${fmt(l.weekly_usage)}/wk · have ${fmt(l.on_hand)} · on order ${fmt(l.on_order)}${l.previous != null ? ` · last ${fmt(l.previous)}` : ""}${l.large_change ? " · ⚠ big change" : ""}`;

export async function recommend(el) {
  const b = await biz();
  const place = b.locations.find((l) => l.holding);
  const body = frame(el, "recommend", place ? `From weekly usage, delivered to ${place.name}.` : "");
  if (!place) { body.innerHTML = '<div class="card"><p>Supplier orders arrive at a holding place - set one up first.</p></div>'; return; }
  const [rec, items] = await Promise.all([api(`/orders/recommendation?location_id=${place.id}`), catalogue(notFinished)]);
  const groups = new Map();
  rec.lines.forEach((l) => { const k = l.supplier_id || ""; if (!groups.has(k)) groups.set(k, { name: l.supplier_name || "No supplier set", lines: [] }); groups.get(k).lines.push(l); });
  if (!rec.has_history) body.append(h("p", { class: "kit-pill warn" }, "No usage history yet - type the quantities"));
  for (const [sid, g] of groups) body.append(supplierCard(sid, g, items, place));
  if (!groups.size) body.innerHTML = '<div class="card"><p class="muted">Nothing to recommend yet.</p></div>';
}

function supplierCard(sid, g, items, place) {
  const card = h("section", { class: "card accent k-section" });
  card.innerHTML = String(html`<div class="k-bar"><h2 class="grow">${g.name}</h2>${pill(`${g.lines.length} items`, "info")}</div><div class="slot"></div>
    ${sid ? html`<p><button class="btn primary" data-save>Save purchase order</button></p>` : html`<p class="muted">Give these items a supplier in Setup to order them.</p>`}`);
  const builder = new Builder({ items, title: "Add more", label: "Order",
    lines: g.lines.map((l) => ({ item_id: l.item_id, name: l.name, unit: l.unit, qty: l.recommended ?? "", hint: hint(l) })) });
  builder.mount(card.querySelector(".slot"));
  card.querySelector("[data-save]")?.addEventListener("click", async () => {
    const lines = builder.lines();
    if (!lines.length) return toast("Add at least one line.");
    const po = await run(() => api("/orders", { method: "POST", body: { supplier_id: sid, location_id: place.id, lines } }), "Purchase order saved");
    if (po) location.hash = `#/orders/${po.po_id}`;
  });
  return card;
}
