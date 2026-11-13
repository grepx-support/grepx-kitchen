/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// Warehouse in: orders to receive (one tap opens the quantities), what the week needs, and receiving without an order
// (with expiry, batch and bin per line - the warehouse files it as a lot).
import { api, run, toast } from "/assets/app.js";
import { barList, Builder, html, icon, pill } from "/assets/kit/index.js";
import { biz } from "../lib/business.js";
import { fmt } from "../lib/format.js";
import { catalogue } from "../lib/items.js";
import { picker } from "../lib/place.js";
import { receive } from "../orders/common.js";
import { frame } from "./common.js";

export async function warehouseIn(el) {
  const b = await biz();
  const place = b.locations.find((l) => l.holding);
  const body = frame(el, "in", { title: "Warehouse in", subtitle: "Receive supplier orders and anything else that arrives." });
  if (!place) { body.innerHTML = '<div class="card"><p>No holding place set up.</p></div>'; return; }
  const [need, open, items] = await Promise.all([api(`/stock/warehouse-in?location_id=${place.id}`).catch(() => ({ lines: [] })),
    api("/orders?state=saved").catch(() => ({ orders: [] })), catalogue()]);
  const needed = need.lines.filter((l) => l.needed > 0);
  body.innerHTML = String(html`<div class="grid two">
    <section class="card accent"><h2>${icon("cart")} Orders to receive</h2>${open.orders.map((o) => html`<div class="k-row">
        <b>${o.number}</b><span>${o.supplier_name} · ${o.lines.length} lines</span><button class="btn small primary" data-receive="${o.id}">Receive</button></div>`)}
      ${open.orders.length ? "" : html`<p class="muted">No open purchase orders.</p>`}</section>
    <section class="card accent"><h2>${icon("alert")} Needed this week ${needed.length ? pill(`${needed.length}`, "bad") : ""}</h2>
      ${barList({ empty: "Nothing needed (or no history yet).", rows: needed.map((l) => ({ label: l.name, value: l.needed, note: `use ${fmt(l.weekly_usage)}/wk · here ${fmt(l.at_holding)} · elsewhere ${fmt(l.elsewhere)} ${l.unit}`, color: "#f43f5e", href: `#/stock?item=${l.item_id}` })) })}</section></div>
    <section class="card accent k-section"><h2>${icon("inbox")} Receive without an order</h2><div class="k-bar">${picker(b.locations, place.id, () => true, "at", "At")}
      <label class="grow">Note<input name="note" placeholder="e.g. bought at the market"></label><button class="btn primary" data-add>Add to stock</button></div><div class="slot"></div></section>`);
  const bins = await api(`/warehouse?location_id=${place.id}`).then((f) => f.bins).catch(() => []);
  const builder = new Builder({ items, title: "Items", label: "Received", scan: true, extras: [
    { name: "expiry", label: "Expiry", type: "date" }, { name: "lot_code", label: "Batch", type: "text" },
    ...(bins.length ? [{ name: "bin_id", label: "Bin", type: "select", options: [["", "-"], ...bins.map((x) => [x.id, x.code])] }] : [])] });
  builder.mount(body.querySelector(".slot"));
  body.querySelectorAll("[data-receive]").forEach((btn) => btn.onclick = async () => {
    if (await receive(open.orders.find((o) => o.id === btn.dataset.receive))) warehouseIn(el);
  });
  body.querySelector("[data-add]").onclick = async () => {
    const lines = builder.lines();
    if (!lines.length) return toast("Add what arrived.");
    if (await run(() => api("/stock/receive", { method: "POST", body: { location_id: body.querySelector('[name="at"]').value, lines, note: body.querySelector('[name="note"]').value } }), "Received")) warehouseIn(el);
  };
}
