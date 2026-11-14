/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// A catering quotation being written: customer, the event, menu lines with prices (the invoice line editor), rates,
// how long it is valid. billing-service works out the totals; changing a sent quote makes it a draft again.
import { api, run } from "/assets/app.js";
import { html, icon } from "/assets/kit/index.js";
import { biz } from "../lib/business.js";
import { catalogue } from "../lib/items.js";
import { frame } from "./common.js";
import { LineEditor } from "./lines.js";
import { editCustomer } from "./sales.js";

const field = (label, name, value, attrs = "") => html`<label>${label}<input name="${name}" value="${value ?? ""}" ${attrs}></label>`;

export async function quoteEditor(el, id) {
  const [b, d, items] = await Promise.all([biz(), api("/sales"), catalogue()]);
  const q = id ? await api(`/sales/quotes/${id}`) : null;
  const rate = q?.tax_rate ?? d.billing.tax_rate ?? 0, currency = b.business?.currency || "";
  const body = frame(el, "quotes", q ? `Edit ${q.number || "quotation"}` : "New quotation", "Save it, check the PDF, then send it to the customer.");
  body.innerHTML = String(html`<form class="card accent m-doc"><div class="row">
      <label class="grow">Customer<span class="row"><select name="customer_id" required><option value="">Choose…</option>${d.customers.filter((c) => c.active !== false).map((c) =>
        html`<option value="${c.customer_id}" ${c.customer_id === q?.customer_id ? "selected" : ""}>${c.name}</option>`)}</select>
        <button type="button" class="btn small" data-cust>${icon("plus", { size: 15 })} New</button></span></label>
      ${field("Event", "event_name", q?.event_name, 'placeholder="e.g. Wedding lunch" maxlength="120"')}</div>
    <div class="row">${field("Event date", "event_date", q?.event_date, 'type="date" required')}${field("Start time", "event_time", q?.event_time, 'type="time"')}
      ${field("Guests", "guests", q?.guests, 'type="number" min="0"')}${field("Venue", "venue", q?.venue, 'maxlength="200"')}</div>
    <div class="row">${field("Tax %", "tax_rate", rate, 'type="number" min="0" max="50" step="any"')}${field("Discount %", "discount_rate", q?.discount_rate ?? 0, 'type="number" min="0" max="100" step="any"')}
      ${field("Valid for (days)", "valid_days", q?.valid_days ?? 14, 'type="number" min="1" max="365"')}</div>
    <div data-lines></div><label>Notes on the quotation (menu details, dietary needs, set-up...)<textarea name="notes" rows="3">${q?.notes || ""}</textarea></label>
    <div class="k-nav"><a class="btn" href="#/sales/quotes">Cancel</a><button class="btn primary">${icon("check", { size: 16 })} Save</button></div></form>`);
  const lines = new LineEditor({ items: items.map((i) => ({ id: i.id, name: i.name, unit: i.unit, price: i.price || "" })), currency, taxRate: rate,
    lines: (q?.lines || []).map((l) => ({ ...l, unit_price: (l.unit_price / 100).toFixed(2) })) });
  lines.mount(body.querySelector("[data-lines]"));
  const form = body.querySelector("form");
  form.tax_rate.oninput = () => lines.setTaxRate(form.tax_rate.value);
  body.querySelector("[data-cust]").onclick = async () => { if (await editCustomer()) quoteEditor(el, id); };
  form.onsubmit = async (e) => {
    e.preventDefault();
    const v = Object.fromEntries(new FormData(form));
    const saved = await run(() => api("/sales/quotes", { method: "POST", body: { ...v, quote_id: id, lines: lines.value() } }), "Saved");
    if (saved) location.hash = `#/sales/quote/${saved.quote_id}`;
  };
}
