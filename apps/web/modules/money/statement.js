/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// A customer's statement: every invoice, credit note and payment with the running balance, what is open, by age.
// Print it (or save as PDF from the print dialog) to send to the customer.
import { api } from "/assets/app.js";
import { html, icon } from "/assets/kit/index.js";
import { biz } from "../lib/business.js";
import { badge, cash, frame } from "./common.js";

const AGES = [["current", "Not due yet"], ["1-30", "1-30 days"], ["31-60", "31-60 days"], ["61-90", "61-90 days"], ["90+", "Over 90 days"]];

export async function statementPage(el, id) {
  const [b, s] = await Promise.all([biz(), api(`/sales/customers/${id}/statement`)]);
  const cur = b.business?.currency || "", c = s.customer, bl = b.business?.billing || {};
  const body = frame(el, "customers", `Statement - ${c.name}`, `As of ${s.today}`, html`<button class="btn" data-print>${icon("download", { size: 16 })} Print / PDF</button>`);
  body.innerHTML = String(html`<article class="card m-statement">
    <header><div><h2>${bl.legal_name || b.business?.name}</h2><p class="muted">${(bl.address || "").split("\n").join(" · ")}</p></div>
      <div class="end"><h2>Statement</h2><p class="muted">${s.today}</p></div></header>
    <p><b>${c.name}</b><br><span class="muted">${(c.address || "").split("\n").join(", ")}${c.email ? ` · ${c.email}` : ""}</span></p>
    <table class="m-view"><thead><tr><th>Date</th><th>What</th><th>Number</th><th>Due</th><th class="end">Amount</th><th class="end">Balance</th></tr></thead>
      <tbody>${s.lines.length ? s.lines.map((l) => html`<tr><td>${l.date}</td><td>${l.what}${l.method ? html` <small class="muted">${l.method}</small>` : ""}</td>
        <td><a href="#/sales/invoice/${l.invoice_id}">${l.number}</a></td><td>${l.due}</td><td class="end">${cash(l.amount)}</td><td class="end"><b>${cash(l.balance)}</b></td></tr>`)
        : html`<tr><td colspan="6" class="muted">Nothing invoiced yet.</td></tr>`}</tbody></table>
    <div class="m-ages">${AGES.map(([k, t]) => html`<div class="${k !== "current" && s.ageing[k] ? "late" : ""}"><small>${t}</small><b>${cash(s.ageing[k])}</b></div>`)}
      <div class="due"><small>Total owing</small><b>${cash(s.owed, cur)}</b></div></div>
    ${bl.payment_note ? html`<p class="muted small">${bl.payment_note}</p>` : ""}</article>
    ${s.open.length ? html`<section class="card k-section"><h2>Open invoices</h2>${s.open.map((o) => html`<div class="k-row"><a href="#/sales/invoice/${o.invoice_id}"><b>${o.number}</b></a>
      <span>due ${o.due}</span>${badge(o.due < s.today ? "overdue" : "open")}<b>${cash(o.balance)}</b></div>`)}</section>` : ""}`);
  el.querySelector("[data-print]").onclick = () => window.print();
}
