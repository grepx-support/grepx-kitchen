/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// The monthly money summary for the owner: sales and purchases before tax, what is left (gross profit), the tax
// charged less the tax paid, and money in and out - one row per month, a chart, and a CSV download.
import { api } from "/assets/app.js";
import { html, icon, kpiRow } from "/assets/kit/index.js";
import { cash, frame } from "./common.js";

const MONTH = (m) => new Date(`${m}-01T00:00:00`).toLocaleString(undefined, { month: "short" });

/** Paired bars per month: sales against purchases, on one scale. */
function chart(months) {
  const top = Math.max(1, ...months.flatMap((m) => [m.sales, m.purchases]));
  const h = (v) => `${Math.max(0, v) / top * 100}%`;
  return html`<div class="m-chart" role="img" aria-label="Sales and purchases by month">
    ${months.map((m) => html`<div class="m-col" title="${MONTH(m.month)}: sales ${cash(m.sales)}, purchases ${cash(m.purchases)}, gross ${cash(m.gross)}">
      <div class="m-bars"><i class="s" style="height:${h(m.sales)}"></i><i class="p" style="height:${h(m.purchases)}"></i></div>
      <small>${MONTH(m.month)}</small></div>`)}</div>
    <div class="m-legend"><span><i class="s"></i>Sales</span><span><i class="p"></i>Purchases</span></div>`;
}

function csv(rep) {
  const cols = ["month", "sales", "purchases", "gross", "tax_charged", "tax_paid", "tax_due", "received", "paid"];
  const rows = [cols.join(","), ...[...rep.months, { month: "total", ...rep.year_total }].map((m) => cols.map((c) => c === "month" ? m.month : (m[c] / 100).toFixed(2)).join(","))];
  const a = Object.assign(document.createElement("a"), { href: URL.createObjectURL(new Blob([rows.join("\n")], { type: "text/csv" })), download: `money-${rep.year}.csv` });
  a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 5000);
}

export async function report(el, q) {
  const rep = await api(`/money/report${q.year ? `?year=${encodeURIComponent(q.year)}` : ""}`);
  const t = rep.year_total, cur = rep.currency, tax = rep.tax_label;
  const step = (n) => html`<a class="btn" href="#/money/report?year=${rep.year + n}">${n < 0 ? "‹" : ""} ${rep.year + n} ${n > 0 ? "›" : ""}</a>`;
  const body = frame(el, "report", `Money summary ${rep.year}`, "Sales and purchases before tax, from issued invoices and supplier bills.",
    html`${step(-1)}${step(1)}<button class="btn" data-csv>${icon("download", { size: 16 })} CSV</button>`);
  const neg = (v) => v < 0 ? "bad" : "";
  body.innerHTML = String(html`${kpiRow([
      { label: "Sales", value: cash(t.sales, cur), icon: "receipt", area: "#7c3aed" },
      { label: "Purchases", value: cash(t.purchases, cur), icon: "inbox", area: "#0ea5e9" },
      { label: "Gross profit", value: cash(t.gross, cur), icon: "bolt", area: t.gross < 0 ? "#e11d48" : "#16a34a" },
      { label: `${tax} to pay`, value: cash(t.tax_due, cur), icon: "clipboard", area: "#f59e0b" }])}
    <section class="card k-section"><h2>By month</h2>${chart(rep.months)}</section>
    <section class="card k-section"><table class="m-view m-report"><thead><tr><th>Month</th><th class="end">Sales</th><th class="end">Purchases</th><th class="end">Gross profit</th>
      <th class="end">${tax} charged</th><th class="end">${tax} paid</th><th class="end">${tax} to pay</th><th class="end">Received</th><th class="end">Paid out</th></tr></thead>
      <tbody>${rep.months.map((m) => html`<tr class="${m.invoices || m.bills || m.received || m.paid ? "" : "muted"}"><td>${MONTH(m.month)}</td>
        <td class="end">${cash(m.sales)}</td><td class="end">${cash(m.purchases)}</td><td class="end ${neg(m.gross)}"><b>${cash(m.gross)}</b></td>
        <td class="end">${cash(m.tax_charged)}</td><td class="end">${cash(m.tax_paid)}</td><td class="end ${neg(m.tax_due)}">${cash(m.tax_due)}</td>
        <td class="end">${cash(m.received)}</td><td class="end">${cash(m.paid)}</td></tr>`)}</tbody>
      <tfoot><tr><th>${rep.year}</th><th class="end">${cash(t.sales)}</th><th class="end">${cash(t.purchases)}</th><th class="end ${neg(t.gross)}">${cash(t.gross)}</th>
        <th class="end">${cash(t.tax_charged)}</th><th class="end">${cash(t.tax_paid)}</th><th class="end ${neg(t.tax_due)}">${cash(t.tax_due)}</th>
        <th class="end">${cash(t.received)}</th><th class="end">${cash(t.paid)}</th></tr></tfoot></table>
      <p class="muted small">Gross profit here is sales less purchases in the same month (both before ${tax}); credit notes are taken off sales, drafts and voided documents are left out.
        "${tax} to pay" is ${tax} charged on invoices less ${tax} paid on bills - check with your accountant before filing.</p></section>`);
  el.querySelector("[data-csv]").onclick = () => csv(rep);
}
