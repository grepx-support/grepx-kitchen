/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// Profit per product and per customer for a period: what each item sold for (before tax, after discounts, less credit
// notes) against what it cost. Shows which products earn the money and which are sold below cost.
import { api } from "/assets/app.js";
import { html, icon, kpiRow } from "/assets/kit/index.js";
import { cash, frame } from "./common.js";

const iso = (d) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;

/** The quick periods, worked out from today. */
function presets(now = new Date()) {
  const y = now.getFullYear(), m = now.getMonth(), q = Math.floor(m / 3) * 3;
  return [["month", "This month", iso(new Date(y, m, 1)), iso(now)], ["last", "Last month", iso(new Date(y, m - 1, 1)), iso(new Date(y, m, 0))],
    ["quarter", "This quarter", iso(new Date(y, q, 1)), iso(now)], ["year", "This year", iso(new Date(y, 0, 1)), iso(now)]];
}

const pct = (v) => (v === null || v === undefined ? "-" : `${v.toFixed(1)}%`);
const toneOf = (v) => (v === null || v === undefined ? "" : v < 0 ? "bad" : v < 20 ? "warn" : "good");

function bar(v) {
  const w = v === null || v === undefined ? 0 : Math.min(100, Math.abs(v));
  return html`<div class="m-mbar ${toneOf(v)}"><i style="width:${w}%"></i><span>${pct(v)}</span></div>`;
}

function products(rows) {
  if (!rows.length) return html`<p class="muted">No invoices issued in this period.</p>`;
  const top = Math.max(1, ...rows.map((r) => Math.abs(r.profit)));
  return html`<table class="m-view m-margins"><thead><tr><th>Product</th><th class="end">Sold</th><th class="end">Sales</th><th class="end">Cost</th>
    <th class="end">Profit</th><th>Margin</th><th class="end">Avg price</th></tr></thead><tbody>${rows.map((r) => html`<tr>
    <td><b>${r.name}</b>${r.item_id && !r.cost_from ? html` <span class="kit-pill warn">no cost set</span>` : ""}${r.cost_from === "recipe" ? html` <span class="kit-pill info">recipe cost</span>` : ""}
      <div class="m-share ${r.profit < 0 ? "bad" : ""}"><i style="width:${Math.abs(r.profit) / top * 100}%"></i></div></td>
    <td class="end">${r.item_id ? `${r.qty} ${r.unit}` : "-"}</td><td class="end">${cash(r.revenue)}</td><td class="end">${cash(r.cost)}</td>
    <td class="end ${r.profit < 0 ? "bad" : ""}"><b>${cash(r.profit)}</b></td><td>${bar(r.margin)}</td>
    <td class="end">${r.item_id && Number(r.qty) ? cash(Math.round(r.revenue / Number(r.qty))) : "-"}</td></tr>`)}</tbody></table>`;
}

const customers = (rows) => (rows.length ? html`<table class="m-view m-margins"><thead><tr><th>Customer</th><th class="end">Invoices</th><th class="end">Sales</th>
  <th class="end">Cost</th><th class="end">Profit</th><th>Margin</th></tr></thead><tbody>${rows.map((c) => html`<tr><td><a href="#/sales/customer/${c.customer_id}"><b>${c.name}</b></a></td>
  <td class="end">${c.invoices}</td><td class="end">${cash(c.revenue)}</td><td class="end">${cash(c.cost)}</td>
  <td class="end ${c.profit < 0 ? "bad" : ""}"><b>${cash(c.profit)}</b></td><td>${bar(c.margin)}</td></tr>`)}</tbody></table>` : "");

export async function margins(el, q) {
  const list = presets(), chosen = list.find((p) => p[0] === q.p) || (q.from ? null : list[0]);
  const [from, to] = chosen ? [chosen[2], chosen[3]] : [q.from, q.to || ""];
  const d = await api(`/money/margins?from=${encodeURIComponent(from)}&to=${encodeURIComponent(to)}`);
  const t = d.total, cur = d.currency;
  const body = frame(el, "margins", "Profit by product", `${d.from} to ${d.to} · sales before tax, against what the goods cost`);
  body.innerHTML = String(html`<div class="m-periods"><div class="kit-chips">${list.map(([k, label]) => html`<a class="kit-chip ${chosen?.[0] === k ? "on" : ""}" href="#/money/margins?p=${k}">${label}</a>`)}</div>
      <form class="m-range" data-range><input type="date" name="from" value="${d.from}"><span>to</span><input type="date" name="to" value="${d.to}"><button class="btn">Show</button></form></div>
    ${kpiRow([{ label: "Sales", value: cash(t.revenue, cur), icon: "receipt", area: "#7c3aed" }, { label: "Cost of goods", value: cash(t.cost, cur), icon: "box", area: "#0ea5e9" },
      { label: "Gross profit", value: cash(t.profit, cur), icon: "trend", area: t.profit < 0 ? "#e11d48" : "#16a34a" }, { label: "Margin", value: pct(t.margin), icon: "chart", area: "#f59e0b" }])}
    ${d.below_cost.length ? html`<div class="card k-test bad">${icon("alert")}<div><b>Sold below cost</b><p class="muted small">${d.below_cost.join(", ")} - check the price or the cost.</p></div></div>` : ""}
    ${d.no_cost.length ? html`<div class="card k-test">${icon("info")}<div><b>No cost set</b><p class="muted small">${d.no_cost.join(", ")} show full price as profit. Set a cost in Setup → Items, or a recipe for the products you make.</p></div></div>` : ""}
    <section class="card k-section"><h2>By product</h2>${products(d.products)}</section>
    ${d.customers.length ? html`<section class="card k-section"><h2>By customer</h2>${customers(d.customers)}</section>` : ""}
    <p class="muted small">Cost is each item's cost today times the quantity sold - for products you make, what the recipe's ingredients cost per unit -
      so it is an estimate if your costs changed during the period.</p>`);
  body.querySelector("[data-range]").onsubmit = (e) => {
    e.preventDefault();
    const f = new FormData(e.target);
    location.hash = `#/money/margins?from=${f.get("from")}&to=${f.get("to")}`;
  };
}
