/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// Landed costs on a bill: duty, freight, customs, insurance, labour - each spread over the item lines by value, quantity
// or weight, and either charged on this bill or billed by someone else (then it only goes into the items' cost).
import { html, icon } from "/assets/kit/index.js";

export const KINDS = [["freight", "Freight"], ["duty", "Duty"], ["customs", "Customs / clearing"], ["insurance", "Insurance"], ["labour", "Labour / handling"], ["other", "Other"]];
const SPREADS = [["value", "by value"], ["qty", "by quantity"], ["weight", "by weight"]];

export class LandedEditor {
  constructor(rows = []) { this.rows = rows.map((r) => ({ ...r, amount: r.amount ? (r.amount / 100).toFixed(2) : "" })); }

  mount(el) { this.el = el; this.draw(); }

  row(r, n) {
    const opt = (list, v) => list.map(([k, t]) => html`<option value="${k}" ${k === v ? "selected" : ""}>${t}</option>`);
    return html`<div class="row lc-row" data-n="${n}"><select name="kind" aria-label="Cost">${opt(KINDS, r.kind)}</select>
      <input name="amount" type="number" min="0" step="0.01" value="${r.amount ?? ""}" placeholder="Amount" class="k-num" aria-label="Amount">
      <select name="spread" aria-label="Spread">${opt(SPREADS, r.spread || "value")}</select>
      <label class="check"><input type="checkbox" name="on_bill" ${r.on_bill === false ? "" : "checked"}> on this bill</label>
      <input name="note" value="${r.note || ""}" placeholder="Note (e.g. agent, permit no.)">
      <button type="button" class="kit-iconbtn" data-del aria-label="Remove">${icon("x", { size: 15 })}</button></div>`;
  }

  draw() {
    this.el.innerHTML = String(html`<section class="card k-section lc"><h2>${icon("truck")} Landed costs <small class="muted">spread into what each item really cost</small></h2>
      ${this.rows.map((r, n) => this.row(r, n))}
      <button type="button" class="btn small" data-add>${icon("plus", { size: 15 })} Add duty, freight …</button></section>`);
    this.el.querySelector("[data-add]").onclick = () => { this.read(); this.rows.push({ kind: "freight" }); this.draw(); };
    this.el.querySelectorAll("[data-del]").forEach((b) => b.onclick = () => { this.read(); this.rows.splice(Number(b.closest("[data-n]").dataset.n), 1); this.draw(); });
  }

  read() {
    this.rows = [...this.el.querySelectorAll(".lc-row")].map((d) => ({ kind: d.querySelector("[name=kind]").value, amount: d.querySelector("[name=amount]").value,
      spread: d.querySelector("[name=spread]").value, on_bill: d.querySelector("[name=on_bill]").checked, note: d.querySelector("[name=note]").value }));
    return this.rows;
  }

  value() { return this.read().filter((r) => r.amount); }
}
