/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// Stock: levels and history, warehouse out with suggestions, warehouse in, transfer, adjust, deliveries (INV-01..11).
import { api, esc, run, toast } from "../../app.js";
import { biz, fmt, has, lines, picker, readLines, remember, remembered, wireLines } from "./lib.js";

const holding = (l) => l.holding;
const notHolding = (l) => !l.holding;
async function itemsOf() {
  const s = await api("/stock"); const items = {};
  s.levels.forEach((l) => { items[l.item_id] = { id: l.item_id, name: l.item_name, unit: l.unit }; });
  return { items, levels: s.levels };
}
async function catalogue() {             // every item of the business, for adding lines (stock list only has items held somewhere)
  const s = await api("/stock/items").catch(() => ({ items: [] }));
  return Object.fromEntries(s.items.map((i) => [i.id, i]));
}

export const routes = [
  { path: "/stock", nav: "Stock", auth: "staff", perm: "view_stock", render: async (el, q) => {
    const b = await biz();
    const loc = q.location ?? "";
    const [s, m] = await Promise.all([api(`/stock${loc ? `?location_id=${loc}` : ""}`), api(`/stock/movements?limit=60${loc ? `&location_id=${loc}` : ""}`)]);
    el.innerHTML = `<h1>Stock</h1><div class="row"><div><label>Location</label><select id="loc"><option value="">All locations</option>${b.locations.map((l) => `<option value="${esc(l.id)}" ${l.id === loc ? "selected" : ""}>${esc(l.name)}</option>`).join("")}</select></div></div>
      <div class="card"><table><tr><th>Location</th><th>Item</th><th>Qty</th></tr>${s.levels.map((r) => `<tr><td>${esc(r.location_name)}</td><td>${esc(r.item_name)}</td><td class="${r.qty < 0 ? "bad" : ""}">${fmt(r.qty)} ${esc(r.unit)}</td></tr>`).join("") || '<tr><td colspan="3" class="muted">No stock recorded yet.</td></tr>'}</table></div><br>
      <div class="card"><h2>History</h2><p class="muted small">Every change with who, when and why. Nobody can edit it.</p><table><tr><th>When</th><th>What</th><th>Item</th><th>Change</th><th>By</th></tr>
      ${m.movements.map((r) => `<tr><td class="small">${esc((r.at || "").slice(0, 16).replace("T", " "))}</td><td>${esc(r.kind.replace("_", " "))} <span class="muted small">${esc(r.location_name || "")}${r.other_location_name ? " ↔ " + esc(r.other_location_name) : ""}</span>${r.note ? `<div class="muted small">${esc(r.note)}</div>` : ""}</td>
        <td>${esc(r.item_name)}</td><td class="${r.qty < 0 ? "bad" : "ok"}">${r.qty > 0 ? "+" : ""}${fmt(r.qty)}</td><td class="small">${esc(r.user_name || "")}</td></tr>`).join("")}</table></div>`;
    el.querySelector("#loc").onchange = (e) => { location.hash = `#/stock?location=${e.target.value}`; };
  } },
  { path: "/stock/out", nav: "Warehouse out", auth: "staff", perm: "warehouse_out", render: async function draw(el, q) {
    const b = await biz();
    const to = q.to || remembered(b.locations, notHolding);
    const from = remembered(b.locations, holding) && b.locations.find(holding)?.id;
    if (!to || !from) { el.innerHTML = '<div class="card"><p>Set up a holding place and at least one other location first.</p></div>'; return; }
    const [plan, all] = await Promise.all([api(`/stock/warehouse-out?to_location_id=${to}`), itemsOf()]);
    const items = { ...all.items, ...(await catalogue()) };
    el.innerHTML = `<h1>Warehouse out</h1><form id="f" class="card"><div class="row"><div><label>From</label>${picker(b.locations, plan.from_location_id || from, holding, "from")}</div>
      <div><label>To</label>${picker(b.locations, to, notHolding, "to")}</div></div>
      <p class="muted">Suggested: enough for ${esc(plan.days_of_cover)} days at this location${plan.has_history ? ` (from ${esc(plan.history_days)} days of usage)` : " - no usage history yet, add lines by hand"}. Accept, change or remove lines.</p>
      ${lines(plan.lines.map((l) => ({ item_id: l.item_id, item_name: l.name, unit: l.unit, qty: l.suggested, hint: `there ${fmt(l.at_location)} · warehouse ${fmt(l.at_holding)}` })), items, { label: "Send" })}
      <p><button class="btn primary">Send stock</button></p></form>`;
    wireLines(el, items);
    el.querySelector('[name="to"]').onchange = (e) => draw(el, { to: e.target.value });
    el.querySelector("#f").onsubmit = async (e) => { e.preventDefault(); const f = new FormData(e.target); const ls = readLines(e.target);
      if (!ls.length) return toast("Nothing to send.");
      if (await run(() => api("/stock/send", { method: "POST", body: { from_location_id: f.get("from"), to_location_id: f.get("to"), lines: ls } }), "Sent")) draw(el, { to }); };
  } },
  { path: "/stock/in", nav: "Warehouse in", auth: "staff", perm: "warehouse_in", render: async function draw(el) {
    const b = await biz();
    const place = b.locations.find(holding);
    if (!place) { el.innerHTML = '<div class="card"><p>No holding place set up.</p></div>'; return; }
    const [need, open, all] = await Promise.all([api(`/stock/warehouse-in?location_id=${place.id}`).catch(() => ({ lines: [] })),
      api("/orders?state=saved").catch(() => ({ orders: [] })), itemsOf()]);
    const items = { ...all.items, ...(await catalogue()) };
    el.innerHTML = `<h1>Warehouse in</h1>
      <div class="card"><h2>Orders to receive</h2>${open.orders.map((o) => `<div class="item"><b>${esc(o.number)}</b> ${esc(o.supplier_name)} · ${o.lines.length} lines <a class="btn small" href="#/orders/${esc(o.id)}">Receive</a></div>`).join("") || '<p class="muted">No open purchase orders.</p>'}</div><br>
      <div class="card"><h2>Needed this week</h2><p class="muted small">All locations' demand for the coming week, beyond the stock already held.</p><table><tr><th>Item</th><th>Weekly use</th><th>Here</th><th>Elsewhere</th><th>Needed</th></tr>
        ${need.lines.map((l) => `<tr><td>${esc(l.name)}</td><td>${fmt(l.weekly_usage)}</td><td>${fmt(l.at_holding)}</td><td>${fmt(l.elsewhere)}</td><td><b>${fmt(l.needed)}</b> ${esc(l.unit)}</td></tr>`).join("") || '<tr><td colspan="5" class="muted">Nothing needed (or no history yet).</td></tr>'}</table></div><br>
      <form id="f" class="card"><h2>Receive without an order</h2><div class="row"><div><label>At</label>${picker(b.locations, place.id, () => true, "at")}</div></div>
        ${lines([], items, { label: "Received" })}<label>Note</label><input name="note" placeholder="e.g. bought at the market"><p><button class="btn primary">Add to stock</button></p></form>`;
    wireLines(el.querySelector("#f"), items);
    el.querySelector("#f").onsubmit = async (e) => { e.preventDefault(); const f = new FormData(e.target); const ls = readLines(e.target);
      if (!ls.length) return toast("Add what arrived.");
      if (await run(() => api("/stock/receive", { method: "POST", body: { location_id: f.get("at"), lines: ls, note: f.get("note") } }), "Received")) draw(el); };
  } },
  { path: "/stock/move", nav: "Transfer", auth: "staff", perm: "transfer", render: async function draw(el) {
    const b = await biz(); const all = await itemsOf(); const items = { ...all.items, ...(await catalogue()) };
    const first = b.locations[0]?.id || "", second = b.locations[1]?.id || first;
    el.innerHTML = `<h1>Transfer and adjust</h1><form id="t" class="card"><h2>Move stock between locations</h2><div class="row"><div><label>From</label>${picker(b.locations, first, () => true, "from")}</div><div><label>To</label>${picker(b.locations, second, () => true, "to")}</div></div>
      ${lines([], items, { label: "Move" })}<p><button class="btn primary">Transfer</button></p></form><br>
      ${has("adjust_stock") ? `<form id="a" class="card"><h2>Adjust stock</h2><p class="muted">Correct a counting error: enter the right quantity. A reason is required.</p>
        <div class="row"><div><label>At</label>${picker(b.locations, first, () => true, "at")}</div></div>${lines([], items, { label: "Correct qty" })}
        <label>Reason</label><input name="note" required minlength="3" placeholder="e.g. miscounted yesterday"><p><button class="btn primary">Adjust</button></p></form>` : ""}`;
    wireLines(el.querySelector("#t"), items);
    el.querySelector("#t").onsubmit = async (e) => { e.preventDefault(); const f = new FormData(e.target); const ls = readLines(e.target);
      if (!ls.length) return toast("Add what to move.");
      if (await run(() => api("/stock/transfer", { method: "POST", body: { from_location_id: f.get("from"), to_location_id: f.get("to"), lines: ls } }), "Moved")) draw(el); };
    const a = el.querySelector("#a");
    if (a) { wireLines(a, items); a.onsubmit = async (e) => { e.preventDefault(); const f = new FormData(a); const ls = readLines(a, true);
      if (!ls.length) return toast("Add the item to correct.");
      if (await run(() => api("/stock/adjust", { method: "POST", body: { location_id: f.get("at"), lines: ls, note: f.get("note") } }), "Adjusted")) draw(el); }; }
  } },
  { path: "/stock/deliveries", nav: "Deliveries", auth: "staff", perm: "delivery", render: async (el) => {
    const today = new Date().toISOString().slice(0, 10);
    const d = await api(`/stock/deliveries`);
    el.innerHTML = `<h1>Deliveries</h1>${d.deliveries.map((t) => `<div class="card"><h2>${esc(t.from)} → ${esc(t.to)}</h2><p class="muted">${esc(t.date)} ${esc((t.at || "").slice(11, 16))} · sent by ${esc(t.by)}${t.date === today ? ' <span class="badge">today</span>' : ""}</p>
      ${t.lines.map((l) => `<div class="item"><b>${fmt(l.qty)} ${esc(l.unit)}</b> ${esc(l.item_name)}</div>`).join("")}</div><br>`).join("") || '<div class="card"><p class="muted">Nothing has left the warehouse yet.</p></div>'}`;
  } },
];
