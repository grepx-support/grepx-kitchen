/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// One invoice: the editor while it is a draft, then the document with what can be done next (issue, PDF, payments,
// credit note, void). Every number shown after saving comes from billing-service.
import { api, run } from "/assets/app.js";
import { confirm, html, icon, openDialog } from "/assets/kit/index.js";
import { biz } from "../lib/business.js";
import { catalogue } from "../lib/items.js";
import { badge, cash, frame, openPdf } from "./common.js";
import { LineEditor } from "./lines.js";
import { askPayment } from "./payment.js";
import { editCustomer } from "./sales.js";

export async function editor(el, id) {
  const [b, d, items] = await Promise.all([biz(), api("/sales"), catalogue()]);
  const inv = id ? await api(`/sales/invoices/${id}`) : null;
  const rate = inv?.tax_rate ?? d.billing.tax_rate ?? 0, currency = b.business?.currency || "";
  const body = frame(el, "sales", inv ? "Edit draft invoice" : "New invoice", "Save it as a draft, check it, then issue it.");
  body.innerHTML = String(html`<form class="card accent m-doc"><div class="row">
      <label class="grow">Customer<span class="row"><select name="customer_id" required><option value="">Choose…</option>${d.customers.filter((c) => c.active !== false).map((c) =>
        html`<option value="${c.customer_id}" ${c.customer_id === inv?.customer_id ? "selected" : ""}>${c.name}</option>`)}</select>
        <button type="button" class="btn small" data-cust>${icon("plus", { size: 15 })} New</button></span></label>
      <label>Their reference / PO<input name="reference" value="${inv?.reference || ""}" maxlength="60"></label>
      <label>Tax %<input name="tax_rate" type="number" min="0" max="50" step="any" value="${rate}"></label>
      <label>Discount %<input name="discount_rate" type="number" min="0" max="100" step="any" value="${inv?.discount_rate ?? 0}"></label>
      <label>Send goods from<select name="location_id"><option value="">Don't change stock</option>${b.locations.map((l) =>
        html`<option value="${l.id}" ${l.id === inv?.location_id ? "selected" : ""}>${l.name}</option>`)}</select></label></div>
    <div data-lines></div><label>Notes on the invoice<textarea name="notes" rows="2">${inv?.notes || ""}</textarea></label>
    <div class="k-nav"><a class="btn" href="#/sales">Cancel</a><button class="btn primary">${icon("check", { size: 16 })} Save draft</button></div></form>`);
  const lines = new LineEditor({ items: items.map((i) => ({ id: i.id, name: i.name, unit: i.unit, price: i.price || "" })), currency, taxRate: rate,
    lines: (inv?.lines || []).map((l) => ({ ...l, unit_price: (l.unit_price / 100).toFixed(2) })) });
  lines.mount(body.querySelector("[data-lines]"));
  const form = body.querySelector("form");
  form.tax_rate.oninput = () => lines.setTaxRate(form.tax_rate.value);
  body.querySelector("[data-cust]").onclick = async () => { if (await editCustomer()) editor(el, id); };
  form.onsubmit = async (e) => {
    e.preventDefault();
    const v = Object.fromEntries(new FormData(form));
    const saved = await run(() => api("/sales/invoices", { method: "POST", body: { ...v, invoice_id: id, lines: lines.value() } }), "Draft saved");
    if (saved) location.hash = `#/sales/invoice/${saved.invoice_id}`;
  };
}

const facts = (inv) => html`<dl class="kit-facts">${[["Customer", inv.customer_name], ["Date", inv.issued || "not issued"], ["Due", inv.due || "-"],
  ["Reference", inv.reference || "-"], ...(inv.location_name ? [["Goods from", inv.location_name]] : []), ...(inv.corrects_number ? [["Corrects", inv.corrects_number]] : [])].map(([k, v]) => html`<dt>${k}</dt><dd>${v}</dd>`)}</dl>`;

const totals = (inv, cur) => html`<dl class="m-totals"><dt>Subtotal</dt><dd>${cash(inv.subtotal)}</dd>
  ${inv.discount ? html`<dt>Discount ${inv.discount_rate}%</dt><dd>-${cash(inv.discount)}</dd>` : ""}<dt>Tax ${inv.tax_rate}%</dt><dd>${cash(inv.tax)}</dd>
  <dt class="big">Total</dt><dd class="big">${cash(inv.total, cur)}</dd>
  ${inv.paid ? html`<dt>Paid</dt><dd>-${cash(inv.paid)}</dd>` : ""}${inv.credited ? html`<dt>Credited</dt><dd>-${cash(inv.credited)}</dd>` : ""}
  ${inv.kind === "invoice" && inv.state !== "void" ? html`<dt class="big">Owed</dt><dd class="big">${cash(inv.balance, cur)}</dd>` : ""}</dl>`;

function actions(inv) {
  const a = [html`<button class="btn" data-pdf>${icon("download", { size: 16 })} PDF</button>`];
  if (inv.state === "draft") a.push(html`<a class="btn" href="#/sales/edit/${inv.invoice_id}">Edit</a>`, html`<button class="btn primary" data-issue>${icon("send", { size: 16 })} Issue…</button>`);
  if (inv.state === "issued" && inv.kind === "invoice" && inv.customer?.email) a.push(html`<button class="btn" data-remind>${icon("mail", { size: 16 })} Send reminder</button>`);
  if (inv.state === "issued" && inv.kind === "invoice") a.push(html`<button class="btn primary" data-pay>${icon("coin", { size: 16 })} Record payment</button>`, html`<button class="btn" data-credit>Credit note</button>`);
  if ((inv.state === "draft" || inv.state === "issued") && !inv.paid && !inv.credited) a.push(html`<button class="btn danger" data-void>Void</button>`);
  return a;
}

export async function detail(el, id) {
  const [b, inv] = await Promise.all([biz(), api(`/sales/invoices/${id}`)]);
  const cur = b.business?.currency || "";
  const title = `${inv.kind === "credit" ? "Credit note" : "Invoice"} ${inv.number || "(draft)"}`;
  const body = frame(el, "sales", title, inv.customer_name, html`${badge(inv.status)}`);
  body.innerHTML = String(html`<div class="row m-acts">${actions(inv)}</div>
    <div class="grid two"><section class="card">${facts(inv)}</section><section class="card">${totals(inv, cur)}</section></div>
    <section class="card k-section"><h2>Lines</h2><table class="m-view"><thead><tr><th>Description</th><th class="end">Qty</th><th class="end">Unit price</th><th class="end">Amount</th></tr></thead>
      <tbody>${inv.lines.map((l) => html`<tr><td>${l.description}${l.discount && l.discount !== "0" ? html` <small class="muted">-${l.discount}%</small>` : ""}</td>
        <td class="end">${l.qty} ${l.unit}</td><td class="end">${cash(l.unit_price)}</td><td class="end">${cash(l.amount)}</td></tr>`)}</tbody></table></section>
    ${(inv.reminders || []).length ? html`<p class="muted small">Reminders sent: ${inv.reminders.map((r) => `${r.at.slice(0, 10)} (${r.stage === "manual" ? "by hand" : `${r.stage} days late`})`).join(", ")}</p>` : ""}
    ${(inv.payments || []).length ? html`<section class="card k-section"><h2>${icon("coin")} Payments</h2>${inv.payments.map((p) =>
      html`<div class="k-row"><b>${cash(p.amount, cur)}</b><span>${p.date} · ${p.method}${p.reference ? ` · ${p.reference}` : ""}</span><span class="muted">${p.by}</span></div>`)}</section>` : ""}`);
  const again = () => detail(el, id);
  const on = (sel, fn) => body.querySelector(sel)?.addEventListener("click", fn);
  on("[data-pdf]", () => openPdf(`/sales/invoices/${id}/pdf`));
  on("[data-issue]", async () => {
    const box = document.createElement("div");
    box.innerHTML = String(html`<p>Issuing gives it the next invoice number and fixes it: after this, changes are made with a credit note.</p>
      <label class="check"><input type="checkbox" name="send" ${inv.customer?.email ? "checked" : "disabled"}> Email it to ${inv.customer?.email || "the customer (no email on file)"}</label>`);
    if (await openDialog({ title: "Issue invoice", body: box, actions: [{ label: "Cancel", value: "" }, { label: "Issue", value: "ok", primary: true }] }) !== "ok") return;
    if (await run(() => api(`/sales/invoices/${id}/issue`, { method: "POST", body: { send: box.querySelector("[name=send]").checked } }), "Issued")) again();
  });
  on("[data-remind]", async () => {
    if (await confirm({ title: "Send a payment reminder?", text: `An email to ${inv.customer.email} about ${cash(inv.balance, cur)} still owing.`, ok: "Send" })
      && await run(() => api(`/sales/invoices/${id}/remind`, { method: "POST", body: {} }), "Reminder sent")) again();
  });
  on("[data-pay]", async () => {
    const p = await askPayment(`Payment for ${inv.number}`, inv.balance, cur);
    if (p && await run(() => api(`/sales/invoices/${id}/pay`, { method: "POST", body: p }), "Payment recorded")) again();
  });
  on("[data-credit]", async () => {
    if (!await confirm({ title: "Credit note", text: inv.paid || inv.credited ? "Part of this invoice was paid: the credit note will need its lines - ask your accountant, or void and re-issue if nothing was paid."
      : "This makes a credit note for the whole invoice, so the customer owes nothing on it.", ok: "Make credit note" })) return;
    const r = await run(() => api(`/sales/invoices/${id}/credit`, { method: "POST", body: { reason: "Credited" } }), "Credit note made");
    if (r) location.hash = `#/sales/invoice/${r.credit_note.invoice_id}`;
  });
  on("[data-void]", async () => {
    if (await confirm({ title: "Void this invoice?", text: "It stays on record as void; its number is not reused.", ok: "Void", danger: true })
      && await run(() => api(`/sales/invoices/${id}/void`, { method: "POST", body: { reason: "Voided" } }), "Voided")) again();
  });
}
