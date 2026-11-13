/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// The line editor shared by invoices and supplier bills: item or free text, quantity, unit price, discount (%).
// It only collects what is typed and shows a running total; the services work out the real totals.
import { html, icon } from "/assets/kit/index.js";
import { cash } from "./common.js";

export class LineEditor {
  /** items: [{id, name, unit, price}]; lines: initial rows; discount: show the discount column */
  constructor({ items, lines = [], discount = true, currency = "", taxRate = 0 }) {
    Object.assign(this, { items, discount, currency, taxRate: Number(taxRate) || 0 });
    this.rows = lines.length ? lines.map((l) => ({ ...l })) : [{}];
  }

  mount(el) { this.el = el; this.draw(); }

  row(r, n) {
    return html`<tr data-n="${n}"><td><select name="item_id" aria-label="Item"><option value="">Other (type below)</option>${this.items.map((i) =>
        html`<option value="${i.id}" ${i.id === r.item_id ? "selected" : ""}>${i.name}</option>`)}</select>
        <input name="description" value="${r.description || ""}" placeholder="Description" aria-label="Description"></td>
      <td><input name="qty" type="number" min="0" step="any" value="${r.qty ?? ""}" class="k-num" aria-label="Quantity"></td>
      <td><input name="unit_price" type="number" min="0" step="0.01" value="${r.unit_price ?? ""}" class="k-num" aria-label="Unit price"></td>
      ${this.discount ? html`<td><input name="discount" type="number" min="0" max="100" step="any" value="${r.discount ?? ""}" class="k-num" aria-label="Discount %"></td>` : ""}
      <td class="end" data-amount></td><td><button type="button" class="kit-iconbtn" data-del aria-label="Remove line">${icon("x", { size: 15 })}</button></td></tr>`;
  }

  draw() {
    this.el.innerHTML = String(html`<div class="kit-scroll"><table class="m-lines"><thead><tr><th>Item / description</th><th class="end">Qty</th><th class="end">Unit price</th>
      ${this.discount ? html`<th class="end">Disc %</th>` : ""}<th class="end">Amount</th><th></th></tr></thead><tbody>${this.rows.map((r, n) => this.row(r, n))}</tbody></table></div>
      <div class="m-linefoot"><button type="button" class="btn small" data-add>${icon("plus", { size: 15 })} Add line</button><div class="m-sum" data-sum></div></div>`);
    this.el.querySelector("[data-add]").onclick = () => { this.read(); this.rows.push({}); this.draw(); };
    this.el.querySelectorAll("[data-del]").forEach((b) => b.onclick = () => { this.read(); this.rows.splice(Number(b.closest("tr").dataset.n), 1); if (!this.rows.length) this.rows.push({}); this.draw(); });
    this.el.querySelectorAll("select[name=item_id]").forEach((s) => s.onchange = () => this.pick(s));
    this.el.oninput = () => this.preview();
    this.preview();
  }

  pick(select) {
    const item = this.items.find((i) => i.id === select.value), tr = select.closest("tr");
    if (!item) return;
    tr.querySelector("[name=description]").value = item.name;
    if (!tr.querySelector("[name=unit_price]").value && item.price) tr.querySelector("[name=unit_price]").value = item.price;
    if (!tr.querySelector("[name=qty]").value) tr.querySelector("[name=qty]").value = 1;
    this.preview();
  }

  read() {
    this.rows = [...this.el.querySelectorAll("tbody tr")].map((tr) => Object.fromEntries([...tr.querySelectorAll("[name]")].map((i) => [i.name, i.value])));
    return this.rows;
  }

  setTaxRate(rate) { this.taxRate = Number(rate) || 0; this.preview(); }

  /** A guide while typing (cents rounded per line, like the service). */
  preview() {
    let sub = 0;
    this.el.querySelectorAll("tbody tr").forEach((tr) => {
      const v = (n) => Number(tr.querySelector(`[name=${n}]`)?.value || 0);
      const gross = Math.round(v("qty") * Math.round(v("unit_price") * 100));
      const amount = gross - Math.round(gross * v("discount") / 100);
      sub += amount;
      tr.querySelector("[data-amount]").textContent = amount ? cash(amount) : "";
    });
    const tax = Math.round(sub * this.taxRate / 100);
    this.el.querySelector("[data-sum]").innerHTML = String(html`<span>Subtotal <b>${cash(sub)}</b></span><span>Tax ${this.taxRate}% <b>${cash(tax)}</b></span>
      <span class="m-total">Total <b>${cash(sub + tax, this.currency)}</b></span>`);
  }

  /** Lines to send: rows with something in them. */
  value() { return this.read().filter((r) => r.description || r.item_id || r.qty); }
}
