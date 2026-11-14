/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// Supplier bills: what is due when, orders received but not billed yet, every bill; the bill editor (from an order:
// lines filled from what was received) and one bill with its three-way match, approval and payments.
import { api, run } from "/assets/app.js";
import { DataTable, empty, html, icon, kpiRow, openDialog, pill } from "/assets/kit/index.js";
import { biz } from "../lib/business.js";
import { catalogue } from "../lib/items.js";
import { today } from "../lib/format.js";
import { badge, cash, frame, openPdf } from "./common.js";
import { LandedEditor, KINDS } from "./landed.js";
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
    <div data-lines></div><div data-landed></div><label class="check"><input type="checkbox" name="recost" checked> When approved, update each item's cost to what it really cost</label><label>Notes<textarea name="notes" rows="2"></textarea></label>
    <div class="k-nav"><a class="btn" href="#/bills">Cancel</a><button class="btn primary">${icon("check", { size: 16 })} Save and check</button></div></form>`);
  const lines = new LineEditor({ items: items.map((i) => ({ id: i.id, name: i.name, unit: i.unit, price: i.cost })), discount: false, currency, taxRate: rate,
    lines: (from?.lines || []).map((l) => ({ ...l, unit_price: Number(l.unit_price).toFixed(2) })) });
  lines.mount(body.querySelector("[data-lines]"));
  const landed = new LandedEditor();
  landed.mount(body.querySelector("[data-landed]"));
  const form = body.querySelector("form");
  form.tax_rate.oninput = () => lines.setTaxRate(form.tax_rate.value);
  form.onsubmit = async (e) => {
    e.preventDefault();
    const v = Object.fromEntries(new FormData(form));
    const saved = await run(() => api("/bills", { method: "POST", body: { ...v, po_id: from?.po_id || "", lines: lines.value(), landed: landed.value(), recost: form.recost.checked } }), "Saved");
    if (saved) location.hash = `#/bills/${saved.bill_id}`;
  };
}

const KIND = Object.fromEntries(KINDS);
const REASON = { damaged: "Damaged", short_dated: "Short-dated", wrong_item: "Wrong item", quality: "Quality", over_delivered: "Too many delivered", other: "Other" };

/** Send goods on this bill back: how many of each (up to what is left to return), why, and the place they leave from. */
async function returnGoods(x, places) {
  const back = {};
  (x.returns || []).forEach((r) => r.lines.forEach((l) => { back[l.item_id] = (back[l.item_id] || 0) + Number(l.qty); }));
  const lines = x.lines.filter((l) => l.item_id);
  const box = document.createElement("form");
  box.innerHTML = String(html`<table class="m-view"><thead><tr><th>Item</th><th class="end">Billed</th><th class="end">Send back</th></tr></thead><tbody>
      ${lines.map((l) => { const left = Number(l.qty) - (back[l.item_id] || 0);
        return html`<tr><td>${l.description}</td><td class="end">${left} ${l.unit}</td><td class="end"><input name="${l.item_id}" type="number" min="0" max="${left}" step="any" class="k-num" ${left > 0 ? "" : "disabled"}></td></tr>`; })}</tbody></table>
    <div class="row"><label>Why<select name="reason">${Object.entries(REASON).map(([k, t]) => html`<option value="${k}">${t}</option>`)}</select></label>
      <label>Leaves stock at<select name="location_id"><option value="">(not in stock)</option>${places.map((p) => html`<option value="${p.id}" ${p.holding ? "selected" : ""}>${p.name}</option>`)}</select></label></div>
    <label>Note<input name="note" maxlength="200" placeholder="RMA / credit note no."></label>`);
  if (await openDialog({ title: `Return to ${x.supplier_name}`, body: box, actions: [{ label: "Cancel", value: "" }, { label: "Return", value: "ok", primary: true }] }) !== "ok") return false;
  const picked = lines.map((l) => ({ item_id: l.item_id, qty: box.elements[l.item_id]?.value })).filter((l) => Number(l.qty) > 0);
  return run(() => api(`/bills/${x.bill_id}/return`, { method: "POST", body: { lines: picked, reason: box.reason.value, location_id: box.location_id.value, note: box.note.value } }), "Returned - credit recorded");
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
      ${x.state !== "void" && x.lines.some((l) => l.item_id) ? html`<button class="btn" data-return>${icon("swap", { size: 16 })} Return goods…</button>` : ""}
      ${["entered", "approved"].includes(x.state) && !x.paid ? html`<button class="btn danger" data-void>Void</button>` : ""}</div>
    <section class="card accent k-section m-match ${x.match}"><h2>${icon(x.match === "check" ? "alert" : "check")} Three-way match: ${badge(x.match)}</h2>
      ${x.match === "matched" ? html`<p>Billed quantities are what was received, at the expected prices.</p>` : x.match === "no_order" ? html`<p class="muted">Not linked to an order - nothing to match.</p>`
        : html`<ul>${x.issues.map((i) => html`<li><b>${i.item_name}</b>: ${ISSUE[i.issue]}${i.billed ? ` (billed ${i.billed}, received ${i.received})` : ""}${i.billed_price ? ` (${cash(i.billed_price)} vs ${cash(i.expected_price)})` : ""}</li>`)}</ul>`}
      ${x.approval_note ? html`<p class="muted">Approved by ${x.approved_by}: ${x.approval_note}</p>` : ""}</section>
    <div class="grid two"><section class="card"><dl class="kit-facts"><dt>Date</dt><dd>${x.bill_date}</dd><dt>Due</dt><dd>${x.due}</dd><dt>Entered by</dt><dd>${x.entered_by}</dd></dl></section>
      <section class="card"><dl class="m-totals"><dt>Subtotal</dt><dd>${cash(x.subtotal)}</dd><dt>Tax ${x.tax_rate}%</dt><dd>${cash(x.tax)}</dd>
        ${x.landed_on_bill ? html`<dt>Landed costs on this bill</dt><dd>${cash(x.landed_on_bill)}</dd>` : ""}
        <dt class="big">Total</dt><dd class="big">${cash(x.total, cur)}</dd>${x.paid ? html`<dt>Paid</dt><dd>-${cash(x.paid)}</dd>` : ""}
        ${x.credited ? html`<dt>Credited for returns</dt><dd>-${cash(x.credited)}</dd>` : ""}
        <dt class="big">To pay</dt><dd class="big">${cash(Math.max(0, x.total - x.paid - (x.credited || 0)), cur)}</dd>
        ${x.refund_due ? html`<dt class="big good">They owe you</dt><dd class="big good">${cash(x.refund_due, cur)}</dd>` : ""}</dl></section></div>
    <section class="card k-section"><h2>Lines</h2><table class="m-view"><thead><tr><th>Description</th><th class="end">Qty</th><th class="end">Unit price</th><th class="end">Amount</th>${x.landed_total ? html`<th class="end">+ Landed</th><th class="end">Real unit cost</th>` : ""}</tr></thead>
      <tbody>${x.lines.map((l) => html`<tr class="${l.item_id ? "k-click" : ""}" data-item="${l.item_id || ""}"><td>${l.description}</td><td class="end">${l.qty} ${l.unit}</td><td class="end">${cash(l.unit_price)}</td><td class="end">${cash(l.amount)}</td>
        ${x.landed_total ? html`<td class="end">${l.landed ? cash(l.landed) : ""}</td><td class="end"><b>${l.item_id ? cash(Number(l.landed_unit)) : ""}</b></td>` : ""}</tr>`)}</tbody></table></section>
    ${x.landed_total ? html`<section class="card k-section"><h2>${icon("truck")} Landed costs · ${cash(x.landed_total, cur)}</h2><table class="m-view"><tbody>
      ${x.landed_costs.map((c) => html`<tr><td>${KIND[c.kind] || c.kind}</td><td class="muted">spread ${c.spread}${c.note ? ` · ${c.note}` : ""}</td><td>${c.on_bill ? pill("on this bill", "info") : pill("billed separately", "")}</td><td class="end">${cash(c.amount)}</td></tr>`)}
      </tbody></table>${x.recost !== false ? html`<p class="muted small">${x.state === "entered" ? "On approval each item's cost becomes its real unit cost." : "Item costs were updated to the real unit cost."}</p>` : ""}</section>` : ""}
    ${(x.returns || []).length ? html`<section class="card k-section"><h2>${icon("swap")} Returned to ${x.supplier_name}</h2><table class="m-view"><thead><tr><th>Date</th><th>Goods</th><th>Why</th><th class="end">Credit</th></tr></thead>
      <tbody>${x.returns.map((r) => html`<tr><td>${r.date}</td><td>${r.lines.map((l) => `${l.qty} × ${l.description}`).join(", ")}</td><td>${pill(REASON[r.reason] || r.reason, "warn")} <span class="muted">${r.note}</span></td><td class="end">${cash(r.credit)}</td></tr>`)}</tbody></table></section>` : ""}`);
  body.querySelectorAll("tr[data-item]").forEach((tr) => tr.dataset.item && (tr.onclick = () => { location.hash = `#/setup?tab=items&edit=${tr.dataset.item}`; }));
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
  on("[data-return]", () => returnGoods(x, b.locations || []).then((ok) => ok && again()));
  on("[data-void]", async () => { if (await run(() => api(`/bills/${id}/void`, { method: "POST", body: { reason: "Voided" } }), "Voided")) again(); });
}
