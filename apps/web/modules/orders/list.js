/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// Orders as a list: stage tabs with counts, search (number, supplier, item), supplier and date filters - all kept in the
// address so Back returns here. Click a row (or press Enter) to open its details in place; J / K move between rows.
// 50 rows at a time ("Show more"), so the page stays short as orders grow.
import { api } from "/assets/app.js";
import { html, icon } from "/assets/kit/index.js";
import { biz } from "../lib/business.js";
import { money, stamp } from "../lib/format.js";
import { frame } from "./common.js";
import { Expander } from "./expander.js";
import { STAGES, stagePill } from "./stages.js";

const matches = (o, q) => {
  const text = `${o.number} ${o.supplier_name} ${o.location_name} ${o.lines.map((l) => l.item_name).join(" ")}`.toLowerCase();
  return (!q.stage || o.stage === q.stage) && (!q.supplier || o.supplier_id === q.supplier) && (!q.q || text.includes(q.q.toLowerCase()))
    && (!q.from || o.created_at.slice(0, 10) >= q.from) && (!q.to || o.created_at.slice(0, 10) <= q.to);
};

const link = (q, extra) => `#/orders/list?${new URLSearchParams(Object.entries({ ...q, ...extra }).filter(([, v]) => v))}`;

function bar(all, q) {
  const suppliers = [...new Map(all.map((o) => [o.supplier_id, o.supplier_name])).entries()].sort((a, z) => a[1].localeCompare(z[1]));
  const count = (s) => all.filter((o) => matches(o, { ...q, stage: s })).length;
  return html`<div class="o-bar"><div class="kit-chips"><a class="kit-chip ${q.stage ? "" : "on"}" href="${link(q, { stage: "" })}">All <b>${count("")}</b></a>
      ${Object.entries(STAGES).map(([k, s]) => html`<a class="kit-chip ${q.stage === k ? "on" : ""}" href="${link(q, { stage: k })}">${s.label} <b>${count(k)}</b></a>`)}</div>
    <label class="kit-search o-search">${icon("search", { size: 15 })}<input data-f="q" value="${q.q || ""}" placeholder="Number, supplier or item"></label>
    <select data-f="supplier" aria-label="Supplier"><option value="">Every supplier</option>${suppliers.map(([id, n]) => html`<option value="${id}" ${q.supplier === id ? "selected" : ""}>${n}</option>`)}</select>
    <input type="date" data-f="from" value="${q.from || ""}" aria-label="From"><input type="date" data-f="to" value="${q.to || ""}" aria-label="To"></div>`;
}

const row = (o, b) => html`<tr class="o-row" data-order="${o.id}" tabindex="0"><td><button type="button" class="kit-iconbtn small o-toggle" tabindex="-1" aria-label="Details">${icon("chevron", { size: 14 })}</button></td>
  <td><a href="#/orders/${o.id}"><b>${o.number}</b></a></td><td>${o.supplier_name}</td><td>${o.location_name || ""}</td><td>${stamp(o.created_at)}</td>
  <td class="end">${o.lines.length}</td><td class="end">${o.value !== undefined ? money(b, o.value) : ""}</td><td>${stagePill(o.stage)}</td></tr>
  <tr class="o-detail" hidden><td colspan="8"><div class="o-more"></div></td></tr>`;

export async function list(el, q) {
  const body = frame(el, "list", "Every purchase order - filter, search, and open any one in place.");
  const [b, d] = await Promise.all([biz(), api("/orders")]);
  const all = d.orders.filter((o) => matches(o, q)), limit = Number(q.n) || 50, shown = all.slice(0, limit);
  body.innerHTML = String(html`${bar(d.orders, q)}<section class="card o-table">${shown.length ? html`<table class="m-view"><thead><tr><th></th><th>Order</th><th>Supplier</th>
    <th>Deliver to</th><th>Made</th><th class="end">Lines</th><th class="end">Value</th><th>Stage</th></tr></thead><tbody>${shown.map((o) => row(o, b))}</tbody></table>`
    : html`<p class="muted">No orders match.</p>`}${all.length > limit ? html`<p class="o-keys"><a class="btn small" href="${link(q, { n: limit + 50 })}">Show ${Math.min(50, all.length - limit)} more of ${all.length - limit}</a></p>` : ""}<p class="muted small o-keys"><kbd>J</kbd> <kbd>K</kbd> move · <kbd>Enter</kbd> details · <kbd>O</kbd> open</p></section>`);
  body.querySelectorAll("[data-f]").forEach((f) => f.addEventListener(f.dataset.f === "q" ? "change" : "input", () => { location.hash = link(q, { [f.dataset.f]: f.value }); }));
  const open = new Expander(b), rows = [...body.querySelectorAll(".o-row")];
  const toggle = (tr) => { const det = tr.nextElementSibling; det.hidden = !det.hidden; open.toggle(tr.dataset.order, det.querySelector(".o-more"), tr); };
  body.addEventListener("click", (e) => { const tr = e.target.closest(".o-row"); if (tr && !e.target.closest("a")) toggle(tr); });
  body.addEventListener("keydown", (e) => {
    const tr = e.target.closest?.(".o-row");
    if (!tr || e.ctrlKey || e.metaKey || e.altKey) return;
    const i = rows.indexOf(tr), go = { j: 1, k: -1, ArrowDown: 1, ArrowUp: -1 }[e.key];
    if (go) { e.preventDefault(); rows[Math.max(0, Math.min(rows.length - 1, i + go))]?.focus(); }
    else if (e.key === "Enter" || e.key === " ") { e.preventDefault(); toggle(tr); }
    else if (e.key === "o") location.hash = `#/orders/${tr.dataset.order}`;
  });
  rows[0]?.focus({ preventScroll: true });
}
