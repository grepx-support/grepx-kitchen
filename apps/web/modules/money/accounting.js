/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// Accounting: the books for a period - every invoice, credit note, bill, return and payment as a balanced journal, the
// trial balance, and files for the accountant (any system, Xero, QuickBooks). Account names can be renamed to match
// the chart of accounts; they are remembered on this device.
import { api } from "/assets/app.js";
import { html, icon, kpiRow, pill } from "/assets/kit/index.js";
import { download } from "../lib/download.js";
import { cash, frame } from "./common.js";

const KEY = "grepx.accounts";
const saved = () => { try { return JSON.parse(localStorage.getItem(KEY) || "{}"); } catch { return {}; } };
const LABEL = { receivable: "Customers owe (receivable)", payable: "You owe suppliers (payable)", sales: "Sales", purchases: "Purchases", tax_out: "Tax collected",
  tax_in: "Tax paid", bank: "Bank", charges: "Delivery / other income", landed: "Freight and duty" };
const monthStart = () => new Date().toISOString().slice(0, 8) + "01";

export async function accounting(el, q) {
  const start = q.start ?? monthStart(), end = q.end ?? new Date().toISOString().slice(0, 10);
  const names = JSON.stringify(saved());
  const d = await api(`/data/accounting?start=${start}&end=${end}&accounts=${encodeURIComponent(names)}`);
  const body = frame(el, "accounting", "Accounting", "The books for your accountant - balanced, ready for Xero, QuickBooks or any system.");
  const debits = d.journal.reduce((a, r) => a + r.debit, 0), credits = d.journal.reduce((a, r) => a + r.credit, 0);
  const qs = `start=${start}&end=${end}&accounts=${encodeURIComponent(names)}`;
  body.innerHTML = String(html`<form class="card accent row" data-range><label>From<input type="date" name="start" value="${start}"></label><label>To<input type="date" name="end" value="${end}"></label>
      <button class="btn">Show</button><span class="grow"></span>${pill(debits === credits ? "balanced" : "NOT balanced", debits === credits ? "good" : "bad")}</form>
    ${kpiRow([{ label: "Entries", value: new Set(d.journal.map((r) => r.ref + r.date)).size, icon: "list" }, { label: "Debits", value: cash(debits, d.currency), icon: "coin" },
      { label: "Credits", value: cash(credits, d.currency), icon: "coin" }])}
    <section class="card k-section"><h2>${icon("download")} Files for your accountant</h2><div class="ac-files">${Object.entries(d.formats).map(([k, t]) => html`<div class="ac-file">
        <b>${t}</b><div class="row"><button class="btn small" data-get="${k}" data-as="xlsx">Excel</button><button class="btn small" data-get="${k}" data-as="csv">CSV</button></div></div>`)}</div></section>
    <div class="grid two"><section class="card k-section"><h2>Trial balance</h2><table class="m-view"><thead><tr><th>Account</th><th class="end">Debit</th><th class="end">Credit</th><th class="end">Balance</th></tr></thead>
        <tbody>${d.trial.map((a) => html`<tr class="k-click" data-acct="${a.account}"><td>${a.account}</td><td class="end">${cash(a.debit)}</td><td class="end">${cash(a.credit)}</td>
          <td class="end ${a.balance < 0 ? "bad" : ""}"><b>${cash(a.balance)}</b></td></tr>`)}</tbody></table></section>
      <section class="card k-section"><h2>${icon("edit")} Account names</h2><p class="muted small">Match your chart of accounts (kept on this device).</p>
        <form data-names>${Object.entries(d.accounts).map(([k, v]) => html`<label>${LABEL[k] || k}<input name="${k}" value="${v}"></label>`)}<button class="btn small primary">Use these names</button></form></section></div>
    <section class="card k-section"><h2>Journal</h2><div class="kit-scroll"><table class="m-view" data-journal><thead><tr><th>Date</th><th>Ref</th><th>Description</th><th>Account</th><th class="end">Debit</th><th class="end">Credit</th></tr></thead>
      <tbody>${d.journal.map((r) => html`<tr data-a="${r.account}"><td>${r.date}</td><td>${r.ref}</td><td>${r.description}</td><td>${r.account}</td><td class="end">${r.debit ? cash(r.debit) : ""}</td><td class="end">${r.credit ? cash(r.credit) : ""}</td></tr>`)}</tbody></table></div></section>`);
  body.querySelector("[data-range]").onsubmit = (e) => { e.preventDefault(); location.hash = `#/money/accounting?start=${e.target.start.value}&end=${e.target.end.value}`; };
  body.querySelector("[data-names]").onsubmit = (e) => { e.preventDefault(); localStorage.setItem(KEY, JSON.stringify(Object.fromEntries(new FormData(e.target)))); accounting(el, q); };
  body.querySelectorAll("[data-get]").forEach((b) => b.onclick = () => download(`/data/accounting/file?format=${b.dataset.get}&file=${b.dataset.as}&${qs}`, `${b.dataset.get}.${b.dataset.as}`));
  body.querySelectorAll("[data-acct]").forEach((tr) => tr.onclick = () => {      // click an account: the journal shows only its lines
    const on = tr.classList.toggle("on");
    body.querySelectorAll("[data-acct]").forEach((o) => o !== tr && o.classList.remove("on"));
    body.querySelectorAll("[data-journal] tbody tr").forEach((r) => { r.hidden = on && r.dataset.a !== tr.dataset.acct; });
    body.querySelector("[data-journal]").scrollIntoView({ behavior: "smooth", block: "start" });
  });
}
