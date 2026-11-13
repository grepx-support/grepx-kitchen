/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// Invoices: what customers owe (by age), this month's figures, every invoice with its status; and the customer list.
import { api, run } from "/assets/app.js";
import { barList, DataTable, empty, html, icon, kpiRow, openDialog } from "/assets/kit/index.js";
import { badge, cash, frame } from "./common.js";

const FILTERS = ["all", "draft", "open", "part paid", "overdue", "paid", "void"];

export async function sales(el, q) {
  const d = await api("/sales");
  const body = frame(el, "sales", "Invoices", "What customers owe you, and every invoice and credit note.",
    html`<a class="btn primary" href="#/sales/new">${icon("plus", { size: 16 })} New invoice</a>`);
  const shown = d.invoices.filter((i) => !q.status || q.status === "all" || i.status === q.status);
  body.innerHTML = String(html`${kpiRow([{ label: "Customers owe", value: cash(d.owed), icon: "coin", area: "#0d9488" },
      { label: "Overdue", value: cash(d.overdue), icon: "alert", area: "#e11d48", tone: d.overdue ? "bad" : "good" },
      { label: "Invoiced this month", value: cash(d.invoiced_month), icon: "receipt", area: "#7c3aed" },
      { label: "Received this month", value: cash(d.received_month), icon: "check", area: "#16a34a" }])}
    <div class="grid two"><section class="card accent"><h2>${icon("clock")} Owed by age</h2>${barList({ rows: Object.entries(d.ageing).map(([k, v]) =>
      ({ label: k === "current" ? "Not due yet" : `${k} days late`, value: v / 100, color: k === "current" ? "#0d9488" : k === "1-30" ? "#f59e0b" : "#e11d48" })) })}</section>
      <section class="card"><h2>${icon("users")} Biggest balances</h2>${top(d.invoices)}</section></div>
    <section class="card k-section"><div class="kit-chips">${FILTERS.map((f) => html`<a class="kit-chip ${(q.status || "all") === f ? "on" : ""}" href="#/sales?status=${f}">${f}</a>`)}</div>
      ${shown.length ? html`<div class="t"></div>` : empty({ icon: "receipt", title: "No invoices here", text: "Create one with New invoice." })}</section>`);
  if (!shown.length) return;
  new DataTable({ rows: shown, columns: [
    { key: "number", label: "Number", render: (i) => html`<a href="#/sales/invoice/${i.invoice_id}"><b>${i.number || "Draft"}</b></a>${i.kind === "credit" ? html` <small class="muted">credit note</small>` : ""}` },
    { key: "customer_name", label: "Customer" }, { key: "issued", label: "Date" }, { key: "due", label: "Due" },
    { key: "total", label: "Total", align: "end", render: (i) => html`${cash(i.kind === "credit" ? -i.total : i.total)}` },
    { key: "balance", label: "Owed", align: "end", render: (i) => html`<b>${i.kind === "credit" || i.state === "void" ? "" : cash(i.balance)}</b>` },
    { key: "status", label: "", render: (i) => html`${badge(i.status)}` }] }).mount(body.querySelector(".t"));
}

function top(invoices) {
  const per = {};
  invoices.filter((i) => i.kind === "invoice" && i.state === "issued").forEach((i) => { per[i.customer_name] = (per[i.customer_name] || 0) + i.balance; });
  const rows = Object.entries(per).sort((a, z) => z[1] - a[1]).slice(0, 5);
  return rows.length ? barList({ rows: rows.map(([k, v]) => ({ label: k, value: v / 100, color: "#7c3aed" })) }) : html`<p class="muted">Nobody owes anything.</p>`;
}

const FIELDS = [["name", "Name", "text", true], ["email", "Email for invoices", "email"], ["phone", "Phone", "tel"], ["contact", "Contact person", "text"],
  ["tax_number", "Tax registration no.", "text"], ["terms_days", "Pays within (days)", "number"]];

async function editCustomer(c = {}) {
  const form = document.createElement("form");
  form.innerHTML = String(html`<div class="m-form">${FIELDS.map(([k, label, type, req]) => html`<label>${label}<input name="${k}" type="${type}" value="${c[k] ?? (k === "terms_days" ? 30 : "")}" ${req ? "required" : ""}></label>`)}
    <label class="m-wide">Billing address<textarea name="address" rows="3">${c.address || ""}</textarea></label></div>`);
  if (await openDialog({ title: c.customer_id ? c.name : "New customer", body: form, actions: [{ label: "Cancel", value: "" }, { label: "Save", value: "ok", primary: true }] }) !== "ok") return null;
  return run(() => api("/sales/customers", { method: "POST", body: { ...Object.fromEntries(new FormData(form)), customer_id: c.customer_id } }), "Saved");
}

export async function customers(el) {
  const d = await api("/sales");
  const owed = {};
  d.invoices.filter((i) => i.kind === "invoice" && i.state === "issued").forEach((i) => { owed[i.customer_id] = (owed[i.customer_id] || 0) + i.balance; });
  const body = frame(el, "customers", "Customers", "Who you invoice, their terms and what they owe.",
    html`<button class="btn primary" data-new>${icon("plus", { size: 16 })} New customer</button>`);
  body.innerHTML = String(d.customers.length ? html`<section class="card"><div class="t"></div></section>`
    : empty({ icon: "users", title: "No customers yet", text: "Add the cafés, caterers or franchisees you sell to." }));
  el.querySelector("[data-new]").onclick = async () => { if (await editCustomer()) customers(el); };
  if (!d.customers.length) return;
  new DataTable({ rows: d.customers, columns: [{ key: "name", label: "Customer", render: (c) => html`<a href="javascript:void 0" data-edit="${c.customer_id}"><b>${c.name}</b></a>` },
    { key: "email", label: "Email" }, { key: "terms_days", label: "Terms", render: (c) => html`${c.terms_days} days` },
    { key: "owed", label: "Owes", align: "end", value: (c) => owed[c.customer_id] || 0, render: (c) => html`<b>${cash(owed[c.customer_id] || 0)}</b>` },
    { key: "statement", label: "", render: (c) => html`<a class="btn small" href="#/sales/customer/${c.customer_id}">Statement</a>` }] })
    .mount(body.querySelector(".t"));
  body.onclick = async (e) => {
    const id = e.target.closest("[data-edit]")?.dataset.edit;
    if (!id) return;
    e.preventDefault();
    if (await editCustomer(d.customers.find((c) => c.customer_id === id))) customers(el);
  };
}

export { editCustomer };
