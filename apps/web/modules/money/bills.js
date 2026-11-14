/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// Supplier bills: what is due when, orders received but not billed yet, every bill; the bill editor (from an order:
// lines filled from what was received) and one bill with its three-way match, approval and payments.
import { api, run } from "/assets/app.js";
import { DataTable, empty, html, icon, kpiRow, openDialog } from "/assets/kit/index.js";
import { biz } from "../lib/business.js";
import { catalogue } from "../lib/items.js";
import { today } from "../lib/format.js";
import { badge, cash, frame, openPdf } from "./common.js";
import { LineEditor } from "./lines.js";
import { askPayment } from "./payment.js";

export async function bills(el) {
  const d = await api("/bills");
  const names = Object.fromEntries(d.suppliers.map((s) => [s.id, s.name]));
  const body = frame(el, "bills", "Supplier bills", "Enter a supplier's invoice, check it against what was ordered and received, approve, pay.",
    html`<a class="btn primary" href="#/bills/new">${icon("plus", { size: 16 })} Enter a bill</a>`);
  body.innerHTML = String(html`${kpiRow([{ label: "Overdue", value: cash(d.due.overdue), icon: "alert", area: "#e11d48", tone: d.due.overdue ? "bad" : "good" },
      { label: "Due this week", value: cash(d.due.this_week), icon: "clock", area: "#f59e0b" }, { label: "Due later", value: cash(d.due.later), icon: "calendar", area: "#0ea5e9" },
      { label: "Waiting for approval", value: d.to_approve, icon: "check", area: "#7c3aed" }])}
    ${d.to_bill.length ? html`<section class="card accent k-section"><h2>${icon("inbox")} Received, not billed yet</h2>${d.to_bill.map((p) => html`<div class="k-row">
      <b>${p.number}</b><span>${names[p.supplier_id] || ""}</span><a class="btn small" href="#/bills/new?po=${p.po_id}">Enter bill</a></div>`)}</section>` : ""}
    <section class="card k-section">${d.bills.length ? html`<div class="t"></div>` : empty({ icon: "inbox", title: "No bills yet", text: "Enter the first one from an order above." })}</section>`);
  if (!d.bills.length) return;
  new DataTable({ onRow: (b) => { location.hash = `#/bills/${b.bill_id}`; }, rows: d.bills, columns: [
    { key: "supplier_name", label: "Supplier", render: (b) => html`<a href="#/bills/${b.bill_id}"><b>${b.supplier_name}</b></a> <small class="muted">${b.supplier_ref}</small>` },
    { key: "po_number", label: "Order" }, { key: "due", label: "Due", render: (b) => html`<span class="${b.overdue ? "bad" : ""}">${b.due}</span>` },
    { key: "total", label: "Total", align: "end", render: (b) => html`${cash(b.total)}` },
    { key: "balance", label: "To pay", align: "end", render: (b) => html`<b>${b.state === "void" ? "" : cash(b.balance)}</b>` },
    { key: "match", label: "Match", render: (b) => html`${badge(b.match)}` }, { key: "state", label: "", render: (b) => html`${badge(b.state)}` }] })
    .mount(body.querySelector(".t"));
}

export async function newBill(el, q) {
  const [b, d, items, from] = await Promise.all([biz(), api("/bills"), catalogue(), q.po ? api(`/bills/from-order/${q.po}`) : null]);
  const currency = b.business?.currency || "", rate = b.business?.billing?.tax_rate ?? 0;
  const body = frame(el, "bills", from ? `Bill for ${from.number}` : "Enter a bill", "Type it as it is on the supplier's invoice; it is checked against the order.");
  body.innerHTML = String(html`<form class="card accent m-doc"><div class="row">
      <label class="grow">Supplier<select name="supplier_id" required>${d.suppliers.map((s) => html`<option value="${s.id}" ${s.id === from?.supplier_id ? "selected" : ""}>${s.name}</option>`)}</select></label>
      <label>Their invoice no.<input name="supplier_ref" required maxlength="40"></label><label>Date<input name="bill_date" type="date" value="${today()}"></label>
      <label>Due<input name="due" type="date" placeholder="30 days"></label><label>Tax %<input name="tax_rate" type="number" min="0" max="50" step="any" value="${rate}"></label></div>
    <div data-lines></div><label>Notes<textarea name="notes" rows="2"></textarea></label>
    <div class="k-nav"><a class="btn" href="#/bills">Cancel</a><button class="btn primary">${icon("check", { size: 16 })} Save and check</button></div></form>`);
  const lines = new LineEditor({ items: items.map((i) => ({ id: i.id, name: i.name, unit: i.unit, price: i.cost })), discount: false, currency, taxRate: rate,
    lines: (from?.lines || []).map((l) => ({ ...l, unit_price: Number(l.unit_price).toFixed(2) })) });
  lines.mount(body.querySelector("[data-lines]"));
  const form = body.querySelector("form");
  form.tax_rate.oninput = () => lines.setTaxRate(form.tax_rate.value);
  form.onsubmit = async (e) => {
    e.preventDefault();
    const v = Object.fromEntries(new FormData(form));
    const saved = await run(() => api("/bills", { method: "POST", body: { ...v, po_id: from?.po_id || "", lines: lines.value() } }), "Saved");
    if (saved) location.hash = `#/bills/${saved.bill_id}`;
  };
}

const ISSUE = { not_ordered: "was not on the order", more_than_received: "billed more than was received", not_received_yet: "order not received yet",
  price_differs: "price differs from the item's cost" };

export async function bill(el, id) {
  const [b, x] = await Promise.all([biz(), api(`/bills/${id}`)]);
  const cur = b.business?.currency || "";
  const body = frame(el, "bills", `${x.supplier_name} · ${x.supplier_ref}`, x.po_number ? `Against order ${x.po_number}` : "No purchase order", html`${badge(x.state)}`);
  body.innerHTML = String(html`<div class="row m-acts"><button class="btn" data-pdf>${icon("download", { size: 16 })} PDF</button>
      ${x.state === "entered" ? html`<button class="btn primary" data-approve>${icon("check", { size: 16 })} Approve…</button>` : ""}
      ${x.state === "approved" ? html`<button class="btn primary" data-pay>${icon("coin", { size: 16 })} Record payment</button>` : ""}
      ${["entered", "approved"].includes(x.state) && !x.paid ? html`<button class="btn danger" data-void>Void</button>` : ""}</div>
    <section class="card accent k-section m-match ${x.match}"><h2>${icon(x.match === "check" ? "alert" : "check")} Three-way match: ${badge(x.match)}</h2>
      ${x.match === "matched" ? html`<p>Billed quantities are what was received, at the expected prices.</p>` : x.match === "no_order" ? html`<p class="muted">Not linked to an order - nothing to match.</p>`
        : html`<ul>${x.issues.map((i) => html`<li><b>${i.item_name}</b>: ${ISSUE[i.issue]}${i.billed ? ` (billed ${i.billed}, received ${i.received})` : ""}${i.billed_price ? ` (${cash(i.billed_price)} vs ${cash(i.expected_price)})` : ""}</li>`)}</ul>`}
      ${x.approval_note ? html`<p class="muted">Approved by ${x.approved_by}: ${x.approval_note}</p>` : ""}</section>
    <div class="grid two"><section class="card"><dl class="kit-facts"><dt>Date</dt><dd>${x.bill_date}</dd><dt>Due</dt><dd>${x.due}</dd><dt>Entered by</dt><dd>${x.entered_by}</dd></dl></section>
      <section class="card"><dl class="m-totals"><dt>Subtotal</dt><dd>${cash(x.subtotal)}</dd><dt>Tax ${x.tax_rate}%</dt><dd>${cash(x.tax)}</dd>
        <dt class="big">Total</dt><dd class="big">${cash(x.total, cur)}</dd>${x.paid ? html`<dt>Paid</dt><dd>-${cash(x.paid)}</dd>` : ""}
        <dt class="big">To pay</dt><dd class="big">${cash(x.total - x.paid, cur)}</dd></dl></section></div>
    <section class="card k-section"><h2>Lines</h2><table class="m-view"><thead><tr><th>Description</th><th class="end">Qty</th><th class="end">Unit price</th><th class="end">Amount</th></tr></thead>
      <tbody>${x.lines.map((l) => html`<tr><td>${l.description}</td><td class="end">${l.qty} ${l.unit}</td><td class="end">${cash(l.unit_price)}</td><td class="end">${cash(l.amount)}</td></tr>`)}</tbody></table></section>`);
  const again = () => bill(el, id);
  const on = (sel, fn) => body.querySelector(sel)?.addEventListener("click", fn);
  on("[data-pdf]", () => openPdf(`/bills/${id}/pdf`));
  on("[data-approve]", async () => {
    const box = document.createElement("div");
    box.innerHTML = String(html`<p>${x.match === "check" ? "This bill does not match the order. Say why it is fine to pay:" : "Ok to pay this bill?"}</p>
      <label>Note<input name="note" ${x.match === "check" ? "required" : ""} maxlength="300"></label>`);
    if (await openDialog({ title: "Approve bill", body: box, actions: [{ label: "Cancel", value: "" }, { label: "Approve", value: "ok", primary: true }] }) !== "ok") return;
    if (await run(() => api(`/bills/${id}/approve`, { method: "POST", body: { note: box.querySelector("input").value } }), "Approved")) again();
  });
  on("[data-pay]", async () => {
    const p = await askPayment(`Pay ${x.supplier_name}`, x.total - x.paid, cur);
    if (p && await run(() => api(`/bills/${id}/pay`, { method: "POST", body: p }), "Payment recorded")) again();
  });
  on("[data-void]", async () => { if (await run(() => api(`/bills/${id}/void`, { method: "POST", body: { reason: "Voided" } }), "Voided")) again(); });
}
