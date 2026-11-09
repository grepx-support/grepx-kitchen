/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// Reorder recommendation -> purchase order; copy as WhatsApp text; change, copy, cancel, receive (ORD-01..10).
import { api, esc, run, toast } from "../../app.js";
import { biz, fmt, has, lines, readLines, wireLines } from "./lib.js";

export const routes = [
  { path: "/orders", nav: "Orders", auth: "staff", perm: "orders", render: async function draw(el) {
    const b = await biz();
    const place = b.locations.find((l) => l.holding);
    if (!place) { el.innerHTML = '<div class="card"><p>Supplier orders arrive at a holding place - set one up first.</p></div>'; return; }
    const [rec, list, sup, cat] = await Promise.all([api(`/orders/recommendation?location_id=${place.id}`), api("/orders"), api("/orders/suppliers"), api("/stock/items")]);
    const suppliers = {};
    rec.lines.forEach((l) => { (suppliers[l.supplier_id || ""] = suppliers[l.supplier_id || ""] || { name: l.supplier_name || "No supplier set", lines: [] }).lines.push(l); });
    const allItems = {}; cat.items.forEach((i) => { if (i.kind !== "finished") allItems[i.id] = { id: i.id, name: i.name, unit: i.unit }; });
    rec.lines.forEach((l) => { allItems[l.item_id] = allItems[l.item_id] || { id: l.item_id, name: l.name, unit: l.unit }; });
    el.innerHTML = `<h1>Orders</h1><p class="muted">Recommended from weekly usage${rec.has_history ? "" : " - no usage history yet: type the quantities"}. Delivered to ${esc(place.name)}.${rec.previous_date ? ` Previous recommendation: ${esc(rec.previous_date)}.` : ""}</p>
      ${Object.entries(suppliers).map(([sid, s]) => `<form class="card po" data-supplier="${esc(sid)}"><h2>${esc(s.name)}</h2>
        ${lines(s.lines.map((l) => ({ item_id: l.item_id, item_name: l.name, unit: l.unit, qty: l.recommended,
          hint: `use ${fmt(l.weekly_usage)}/wk · have ${fmt(l.on_hand)} · on order ${fmt(l.on_order)}${l.previous !== null && l.previous !== undefined ? ` · last time ${fmt(l.previous)}` : ""}${l.large_change ? " · ⚠ large change" : ""}` })), allItems, { label: "Order" })}
        ${sid ? '<p><button class="btn primary">Save purchase order</button></p>' : '<p class="muted">Give these items a supplier in Setup to order them.</p>'}</form><br>`).join("")}
      ${sup.suppliers.length ? `<form class="card po" data-supplier=""><h2>New order</h2><label>Supplier</label><select name="supplier">${sup.suppliers.map((s) => `<option value="${esc(s.id)}">${esc(s.name)}</option>`).join("")}</select>
        ${lines([], allItems, { label: "Order" })}<p><button class="btn primary">Save purchase order</button></p></form><br>` : ""}
      <div class="card"><h2>Purchase orders</h2><table><tr><th>Order</th><th>Supplier</th><th>Status</th><th></th></tr>
        ${list.orders.map((o) => `<tr><td>${esc(o.number)}</td><td>${esc(o.supplier_name)}</td><td><span class="badge">${esc(o.state)}</span></td><td><a href="#/orders/${esc(o.id)}">Open</a></td></tr>`).join("") || '<tr><td colspan="4" class="muted">None yet.</td></tr>'}</table></div>`;
    el.querySelectorAll("form.po").forEach((f) => { wireLines(f, allItems); f.onsubmit = async (e) => { e.preventDefault();
      const ls = readLines(f); const supplier = f.dataset.supplier || new FormData(f).get("supplier");
      if (!ls.length || !supplier) return toast("Add at least one line.");
      const po = await run(() => api("/orders", { method: "POST", body: { supplier_id: supplier, location_id: place.id, lines: ls } }), "Purchase order saved");
      if (po) location.hash = `#/orders/${po.po_id}`; }; });
  } },
  { path: "/orders/:id", auth: "staff", render: async function draw(el, { args }) {
    const o = await api(`/orders/${args[0]}`);
    const open = o.state === "saved";
    const items = {}; o.lines.forEach((l) => { items[l.item_id] = { id: l.item_id, name: l.item_name, unit: l.unit }; });
    el.innerHTML = `<h1>${esc(o.number)} <span class="badge">${esc(o.state)}</span></h1>
      <div class="card"><h2>${esc(o.supplier_name)}</h2><pre id="txt">${esc(o.text)}</pre>
        <p class="row"><button class="btn" id="copy">Copy as text</button>${o.supplier_phone ? `<a class="btn" target="_blank" rel="noopener" href="https://wa.me/${esc(o.supplier_phone.replace(/\D/g, ""))}?text=${encodeURIComponent(o.text)}">Send on WhatsApp</a>` : ""}
        ${has("orders") ? '<button class="btn" id="dup">Copy to a new order</button>' : ""}${open && has("orders") ? '<button class="btn" id="cancel">Cancel order</button>' : ""}</p>
        ${o.value !== undefined ? `<p class="muted">Value at current costs: ${fmt(o.value)}</p>` : ""}</div><br>
      ${open ? `<form id="f" class="card"><h2>Receive or change</h2><p class="muted">Change a quantity if the delivery differs, then receive. Or save changes without receiving.</p>
        ${lines(o.lines.map((l) => ({ item_id: l.item_id, item_name: l.item_name, unit: l.unit, qty: l.qty })), items, { label: "Qty", allowAdd: false })}
        <p class="row"><button class="btn primary" name="go" value="receive">Receive into stock</button>${has("orders") ? '<button class="btn" name="go" value="save">Save changes</button>' : ""}</p></form>`
      : `<div class="card"><h2>Received</h2>${(o.received || []).map((l) => `<div class="item">${fmt(l.qty)} × ${esc(items[l.item_id]?.name || l.item_id)}</div>`).join("") || '<p class="muted">-</p>'}</div>`}`;
    el.querySelector("#copy").onclick = async () => { try { await navigator.clipboard.writeText(o.text); toast("Copied - paste it into WhatsApp"); } catch (e) { toast("Select the text and copy it."); } };
    el.querySelector("#dup")?.addEventListener("click", async () => { const n = await run(() => api(`/orders/${o.id}/copy`, { method: "POST" }), "New order saved"); if (n) location.hash = `#/orders/${n.po_id}`; });
    el.querySelector("#cancel")?.addEventListener("click", async () => { if (await run(() => api(`/orders/${o.id}/cancel`, { method: "POST" }), "Cancelled")) draw(el, { args }); });
    const f = el.querySelector("#f");
    if (f) { wireLines(f, items); f.onsubmit = async (e) => { e.preventDefault(); const go = e.submitter?.value || "receive"; const ls = readLines(f, true);
      const path = go === "receive" ? `/orders/${o.id}/receive` : `/orders/${o.id}`;
      if (await run(() => api(path, { method: "POST", body: { lines: go === "receive" ? ls : ls.filter((l) => l.qty > 0) } }), go === "receive" ? "Received into stock" : "Saved")) draw(el, { args }); }; }
  } },
];
