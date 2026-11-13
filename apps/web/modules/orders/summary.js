/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// Everything about one order in one panel - used where an order is expanded in place (board, list) and on its page:
// who / where / when, each line ordered against received (with values for people who see costs), bills, timeline.
import { html, icon, pill } from "/assets/kit/index.js";
import { fmt, money } from "../lib/format.js";
import { stagePill } from "./stages.js";
import { timelineView } from "./timeline.js";

function lines(o, b) {
  const costs = o.line_view.some((l) => "value" in l);
  const total = o.line_view.reduce((n, l) => n + (l.value || 0), 0);
  return html`<table class="m-view o-lines"><thead><tr><th>Item</th><th class="end">Ordered</th><th class="end">Received</th>
      ${costs ? html`<th class="end">Unit cost</th><th class="end">Value</th>` : ""}</tr></thead>
    <tbody>${o.line_view.map((l) => html`<tr><td><a href="#/stock?item=${l.item_id}">${l.name}</a></td><td class="end">${fmt(l.ordered)} ${l.unit}</td>
      <td class="end">${l.received === null ? html`<span class="muted">-</span>` : html`${fmt(l.received)} ${l.unit}${l.difference ? html` <b class="${l.difference < 0 ? "bad" : "ok"}">(${l.difference > 0 ? "+" : ""}${fmt(l.difference)})</b>` : ""}`}</td>
      ${costs ? html`<td class="end">${fmt(l.unit_cost)}</td><td class="end">${fmt(l.value)}</td>` : ""}</tr>`)}</tbody>
    ${costs ? html`<tfoot><tr><th colspan="4">Value at current costs</th><th class="end">${money(b, total)}</th></tr></tfoot>` : ""}</table>`;
}

const contact = (s) => html`<span>${s.contact ? `${s.contact} · ` : ""}${s.phone ? html`<a href="tel:${s.phone}">${icon("phone", { size: 13 })} ${s.phone}</a>` : ""}
  ${s.email ? html` <a href="mailto:${s.email}">${icon("mail", { size: 13 })} ${s.email}</a>` : ""}</span>`;

export function orderSummary(o, b) {
  return html`<div class="o-sum">
    <div class="o-facts">
      <div><small>Stage</small>${stagePill(o.stage)}</div>
      <div><small>Supplier</small><b>${o.supplier?.name || o.supplier_name}</b>${contact(o.supplier || {})}</div>
      <div><small>Deliver to</small><b>${o.location_name || "-"}</b></div>
      <div><small>Made</small><b>${new Date(o.created_at).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" })}</b><span class="muted small">${o.created_by_name || ""}</span></div>
      ${o.bills?.length ? html`<div><small>Bills</small>${o.bills.map((x) => html`<a href="#/bills/${x.bill_id}">${pill(`${x.ref || "bill"} · ${x.state}`, x.state === "paid" ? "good" : "warn")}</a>`)}</div>` : ""}
    </div>
    <div class="o-cols"><div>${lines(o, b)}${o.note ? html`<p class="o-note">${icon("info", { size: 14 })} ${o.note}</p>` : ""}</div>
      <div><h3>Timeline</h3>${timelineView(o.timeline)}</div></div></div>`;
}
