/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// The four closing steps as views of one draft: count, sales, issues, check (CLS-01..06).
import { html, icon } from "/assets/kit/index.js";
import { fmt } from "../lib/format.js";

export const STEPS = ["Count", "Sales", "Issues", "Check"];

export const count = (f, d) => html`<p class="muted">Type what you count. Leave a box empty if you did not count that item.
    <b>${Object.keys(d.counts).length}</b> of ${f.lines.length} counted.</p>
  <div class="k-count">${f.lines.map((l) => html`<label class="${d.counts[l.item_id] !== undefined ? "done" : ""}">${l.item_name}
    <small>expected ${fmt(l.expected)} ${l.unit}</small><input type="number" inputmode="decimal" min="0" step="any" data-count="${l.item_id}"
      value="${d.counts[l.item_id] ?? ""}" aria-label="Counted ${l.item_name}"></label>`)}</div>`;

export const sales = (f, d) => html`<p class="muted">Takings for ${d.date}, by type.</p><div class="row">${f.sales_types.map((s) => html`<label>${s}
  <input type="number" inputmode="decimal" min="0" step="0.01" data-sale="${s}" value="${d.sales[s] ?? ""}"></label>`)}</div>`;

export const issues = (f, d) => html`<label>Anything the owner should know (optional)<textarea rows="4" data-issues placeholder="e.g. fridge door not closing">${d.issues}</textarea></label>
  <div class="row"><label>Your name<input data-staff value="${d.staff}" required></label><label>Date<input type="date" data-date value="${d.date}" max="${f.date}"></label></div>`;

export function check(f, d) {
  const names = Object.fromEntries(f.lines.map((l) => [l.item_id, l]));
  const total = Object.values(d.sales).reduce((a, n) => a + n, 0);
  return html`<p>${d.staff} · ${d.date} · <b>${Object.keys(d.counts).length}</b> items counted · sales <b>${fmt(total)}</b></p>
    ${Object.entries(d.counts).map(([id, qty]) => { const diff = qty - (names[id]?.expected || 0);
      return html`<div class="k-diff"><span>${names[id]?.item_name}</span><span><b>${fmt(qty)}</b> <span class="${diff < 0 ? "bad" : "ok"}">(${diff > 0 ? "+" : ""}${fmt(diff)})</span></span></div>`; })}
    ${total ? "" : html`<p class="bad">${icon("alert", { size: 16 })} No sales entered.</p>`}${d.issues ? html`<p class="warn">⚠ ${d.issues}</p>` : ""}`;
}
