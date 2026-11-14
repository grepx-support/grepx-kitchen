/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// Catering quotations: the pipeline (how many and how much at each stage, win rate, events coming up) and one quote
// with its next step - send, the customer says yes (an order) or no, then invoice it. billing-service decides each move.
import { api, run } from "/assets/app.js";
import { confirm, DataTable, empty, html, icon, kpiRow, openDialog } from "/assets/kit/index.js";
import { biz } from "../lib/business.js";
import { badge, cash, frame, openPdf } from "./common.js";

const FILTERS = ["all", "draft", "sent", "expired", "ordered", "invoiced", "declined", "cancelled"];
const ask = async (title, text, name, ok = "Save") => {
  const box = document.createElement("div");
  box.innerHTML = String(html`<p>${text}</p><label>${name}<input name="v"></label>`);
  return await openDialog({ title, body: box, actions: [{ label: "Back", value: "" }, { label: ok, value: "ok", primary: true }] }) === "ok" ? box.querySelector("input").value : null;
};

export async function quotes(el, q) {
  const d = await api("/sales/quotes");
  const s = d.stages;
  const body = frame(el, "quotes", "Quotations", "Catering and event quotes: quote, order, invoice.",
    html`<a class="btn primary" href="#/sales/quotes/new">${icon("plus", { size: 16 })} New quotation</a>`);
  const shown = d.quotes.filter((x) => !q.status || q.status === "all" || x.status === q.status);
  body.innerHTML = String(html`${kpiRow([{ label: "Out for a decision", value: cash(s.sent.total), note: `${s.sent.count} sent · ${s.expired.count} expired`, icon: "send", area: "#0891b2" },
      { label: "Orders to deliver", value: cash(s.ordered.total), note: `${s.ordered.count} confirmed`, icon: "calendar", area: "#16a34a" },
      { label: "Invoiced", value: cash(s.invoiced.total), note: `${s.invoiced.count} orders`, icon: "receipt", area: "#7c3aed" },
      { label: "Win rate", value: d.win_rate === null ? "-" : `${d.win_rate}%`, note: `${s.declined.count} declined`, icon: "trend", area: "#e11d48" }])}
    ${d.upcoming.length ? html`<section class="card accent"><h2>${icon("calendar")} Events coming up</h2>${d.upcoming.map((x) =>
      html`<div class="k-row"><b>${x.event_date} ${x.event_time || ""}</b><a href="#/sales/quote/${x.quote_id}">${x.customer_name}${x.event_name ? ` - ${x.event_name}` : ""}</a>
        <span>${x.guests ? `${x.guests} guests` : ""}</span></div>`)}</section>` : ""}
    <section class="card k-section"><div class="kit-chips">${FILTERS.map((f) => html`<a class="kit-chip ${(q.status || "all") === f ? "on" : ""}" href="#/sales/quotes?status=${f}">${f}</a>`)}</div>
      ${shown.length ? html`<div class="t"></div>` : empty({ icon: "receipt", title: "No quotations here", text: "Write one with New quotation." })}</section>`);
  if (!shown.length) return;
  new DataTable({ onRow: (x) => { location.hash = `#/sales/quote/${x.quote_id}`; }, rows: shown, columns: [
    { key: "number", label: "Number", render: (x) => html`<a href="#/sales/quote/${x.quote_id}"><b>${x.order_number || x.number || "Draft"}</b></a>` },
    { key: "customer_name", label: "Customer" }, { key: "event_date", label: "Event", render: (x) => html`${x.event_date} ${x.event_name || ""}` },
    { key: "guests", label: "Guests", align: "end" }, { key: "total", label: "Total", align: "end", render: (x) => html`${cash(x.total)}` },
    { key: "status", label: "", render: (x) => html`${badge(x.status)}` }] }).mount(body.querySelector(".t"));
}

function actions(x) {
  const open = x.state === "draft" || x.state === "sent";
  return [html`<button class="btn" data-pdf>${icon("download", { size: 16 })} PDF</button>`,
    open && html`<a class="btn" href="#/sales/quotes/edit/${x.quote_id}">Edit</a>`,
    open && html`<button class="btn" data-send>${icon("send", { size: 16 })} Send…</button>`,
    open && html`<button class="btn primary" data-accept>${icon("check", { size: 16 })} Customer said yes</button>`,
    open && html`<button class="btn" data-decline>Customer said no</button>`,
    x.state === "ordered" && html`<button class="btn primary" data-invoice>${icon("receipt", { size: 16 })} Make the invoice</button>`,
    (open || x.state === "ordered") && html`<button class="btn danger" data-cancel>Cancel</button>`,
    x.invoice_id && html`<a class="btn" href="#/sales/invoice/${x.invoice_id}">Open the invoice</a>`].filter(Boolean);
}

export async function quote(el, id) {
  const [b, x] = await Promise.all([biz(), api(`/sales/quotes/${id}`)]);
  const cur = b.business?.currency || "";
  const body = frame(el, "quotes", x.order_number ? `Order ${x.order_number}` : `Quotation ${x.number || "(draft)"}`, x.customer_name, html`${badge(x.status)}`);
  const facts = [["Event", `${x.event_name || ""} ${x.event_date} ${x.event_time || ""}`], ["Venue", x.venue || "-"], ["Guests", x.guests || "-"],
    ["Quotation", x.number || "-"], ["Valid until", x.valid_until || "set when sent"], ...(x.order_number ? [["Order", x.order_number], ["Confirmed by", x.accepted_by]] : []),
    ...(x.close_reason ? [["Reason", x.close_reason]] : []), ...(x.revision ? [["Revision", x.revision]] : [])];
  body.innerHTML = String(html`<div class="row m-acts">${actions(x)}</div>
    <div class="grid two"><section class="card"><dl class="kit-facts">${facts.map(([k, v]) => html`<dt>${k}</dt><dd>${v}</dd>`)}</dl></section>
      <section class="card"><dl class="m-totals"><dt>Subtotal</dt><dd>${cash(x.subtotal)}</dd>${x.discount ? html`<dt>Discount</dt><dd>-${cash(x.discount)}</dd>` : ""}
        <dt>Tax ${x.tax_rate}%</dt><dd>${cash(x.tax)}</dd><dt class="big">Total</dt><dd class="big">${cash(x.total, cur)}</dd>
        ${x.per_guest ? html`<dt>Per guest</dt><dd>${cash(x.per_guest, cur)}</dd>` : ""}</dl></section></div>
    <section class="card k-section"><h2>Menu and services</h2><table class="m-view"><thead><tr><th>Description</th><th class="end">Qty</th><th class="end">Unit price</th><th class="end">Amount</th></tr></thead>
      <tbody>${x.lines.map((l) => html`<tr><td>${l.description}</td><td class="end">${l.qty} ${l.unit}</td><td class="end">${cash(l.unit_price)}</td><td class="end">${cash(l.amount)}</td></tr>`)}</tbody></table>
      ${x.notes ? html`<p class="muted">${x.notes}</p>` : ""}</section>
    ${(x.sent || []).length ? html`<p class="muted small">Sent: ${x.sent.map((s) => `${s.at.slice(0, 10)}${s.emailed ? " by email" : ""} (${s.by})`).join(", ")}</p>` : ""}`);
  const again = () => quote(el, id);
  const on = (sel, fn) => body.querySelector(sel)?.addEventListener("click", fn);
  const post = (verb, data, done) => run(() => api(`/sales/quotes/${id}/${verb}`, { method: "POST", body: data }), done);
  on("[data-pdf]", () => openPdf(`/sales/quotes/${id}/pdf`));
  on("[data-send]", async () => {
    const box = document.createElement("div");
    box.innerHTML = String(html`<p>Sending gives it its number and the date it is valid until.</p>
      <label class="check"><input type="checkbox" name="send" ${x.customer?.email ? "checked" : "disabled"}> Email it with the PDF to ${x.customer?.email || "the customer (no email on file)"}</label>`);
    if (await openDialog({ title: "Send quotation", body: box, actions: [{ label: "Cancel", value: "" }, { label: "Send", value: "ok", primary: true }] }) !== "ok") return;
    if (await post("send", { send: box.querySelector("[name=send]").checked }, "Sent")) again();
  });
  on("[data-accept]", async () => {
    const who = await ask("The customer said yes", "It becomes an order with its own number; then make the invoice when it suits you.", "Confirmed by (name)", "Make it an order");
    if (who !== null && await post("accept", { accepted_by: who }, "Order confirmed")) again();
  });
  on("[data-decline]", async () => {
    const why = await ask("The customer said no", "Kept with the quote, so you can see why quotes are lost.", "Why (price, date, went elsewhere...)");
    if (why !== null && await post("decline", { reason: why }, "Marked as declined")) again();
  });
  on("[data-cancel]", async () => {
    if (await confirm({ title: "Cancel this?", text: "It stays on record as cancelled.", ok: "Cancel it", cancel: "Keep it", danger: true })
      && await post("cancel", { reason: "Cancelled" }, "Cancelled")) again();
  });
  on("[data-invoice]", async () => {
    const out = await post("invoice", {}, "Draft invoice made - check it and issue it");
    if (out) location.hash = `#/sales/invoice/${out.invoice_id}`;
  });
}
