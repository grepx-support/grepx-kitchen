/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// Price lists: what each item sells for - its list price, quantity breaks (cheaper per unit from N up), customers who
// have their own price for it - and customers' standing discounts. Invoices and quotes fill prices from these.
import { api, run } from "/assets/app.js";
import { empty, html, icon, openDialog, pill } from "/assets/kit/index.js";
import { frame } from "./common.js";

async function editBreaks(item, again) {
  const box = document.createElement("form");
  const rows = [...item.breaks, { min_qty: "", price: "" }, { min_qty: "", price: "" }];
  box.innerHTML = String(html`<p class="muted">List price ${item.price} a ${item.unit || "unit"}. From these quantities up, one unit costs:</p>
    ${rows.map((b) => html`<div class="row"><label>From qty<input name="q" type="number" min="2" step="any" value="${b.min_qty}"></label>
      <label>Price each<input name="p" type="number" min="0" step="0.01" value="${b.price}"></label></div>`)}`);
  if (await openDialog({ title: `Quantity prices - ${item.name}`, body: box, actions: [{ label: "Cancel", value: "" }, { label: "Save", value: "ok", primary: true }] }) !== "ok") return;
  const q = [...box.querySelectorAll("[name=q]")], p = [...box.querySelectorAll("[name=p]")];
  const breaks = q.map((x, i) => ({ min_qty: x.value, price: p[i].value })).filter((b) => b.min_qty && b.price !== "");
  if (await run(() => api(`/sales/prices/${item.item_id}/breaks`, { method: "PUT", body: { breaks } }), "Saved")) again();
}

async function customerPrice(item, customers, again) {
  const box = document.createElement("form");
  box.innerHTML = String(html`<div class="row"><label>Customer<select name="c">${customers.map((c) => html`<option value="${c.customer_id}">${c.name}</option>`)}</select></label>
    <label>Their price for ${item.name}<input name="p" type="number" min="0" step="0.01" required></label></div>`);
  if (await openDialog({ title: "A customer's own price", body: box, actions: [{ label: "Cancel", value: "" }, { label: "Save", value: "ok", primary: true }] }) !== "ok") return;
  if (await run(() => api(`/sales/customers/${box.c.value}/pricing`, { method: "PUT", body: { item_id: item.item_id, price: box.p.value } }), "Saved")) again();
}

async function discount(customers, again) {
  const box = document.createElement("form");
  box.innerHTML = String(html`<div class="row"><label>Customer<select name="c">${customers.map((c) => html`<option value="${c.customer_id}">${c.name}</option>`)}</select></label>
    <label>Discount on everything %<input name="d" type="number" min="0" max="100" step="any" required></label></div>`);
  if (await openDialog({ title: "A standing discount", body: box, actions: [{ label: "Cancel", value: "" }, { label: "Save", value: "ok", primary: true }] }) !== "ok") return;
  if (await run(() => api(`/sales/customers/${box.c.value}/pricing`, { method: "PUT", body: { discount_pct: box.d.value } }), "Saved")) again();
}

export async function prices(el) {
  const [d, s] = await Promise.all([api("/sales/prices"), api("/sales")]);
  const customers = s.customers.filter((c) => c.active !== false);
  const again = () => prices(el);
  const body = frame(el, "prices", "Price lists", "List prices, quantity prices and customers' own prices - filled into invoices and quotes.",
    html`<button class="btn" data-disc>${icon("users", { size: 16 })} Standing discount…</button>`);
  body.innerHTML = String(html`${d.discounts.length ? html`<section class="card k-section"><h2>Standing discounts</h2>${d.discounts.map((x) => html`${pill(`${x.name}: ${x.discount_pct}% off`, "info")} `)}</section>` : ""}
    ${d.items.length ? html`<section class="card k-section"><table class="m-view pl-table"><thead><tr><th>Item</th><th class="end">List price</th><th>Quantity prices</th><th>Customers' own prices</th></tr></thead><tbody>
      ${d.items.map((i) => html`<tr><td><b>${i.name}</b> <span class="muted small">${i.unit}</span></td><td class="end">${i.price}</td>
        <td><button class="btn small" data-breaks="${i.item_id}">${i.breaks.length ? i.breaks.map((b) => `${b.min_qty}+ @ ${b.price}`).join(" · ") : "+ add"}</button></td>
        <td>${i.customers.map((c) => html`<span class="pl-chip">${c.name} @ ${c.price} <a href="javascript:void 0" data-off="${c.customer_id}" data-item="${i.item_id}" title="Remove">✕</a></span>`)}
          <button class="btn small" data-own="${i.item_id}">+ customer</button></td></tr>`)}</tbody></table></section>`
      : empty({ icon: "coin", title: "Nothing priced yet", text: "Give finished items a sale price in Setup → Items." })}`);
  const find = (id) => d.items.find((i) => i.item_id === id);
  el.querySelector("[data-disc]").onclick = () => discount(customers, again);
  body.addEventListener("click", async (e) => {
    const t = e.target.closest("[data-breaks],[data-own],[data-off]");
    if (!t) return;
    if (t.dataset.breaks) editBreaks(find(t.dataset.breaks), again);
    else if (t.dataset.own) customerPrice(find(t.dataset.own), customers, again);
    else if (await run(() => api(`/sales/customers/${t.dataset.off}/pricing`, { method: "PUT", body: { item_id: t.dataset.item, price: null } }), "Removed")) again();
  });
}
