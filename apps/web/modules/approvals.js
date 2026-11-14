/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// Approvals: everything waiting for your yes or no - big purchase orders, supplier bills (mismatches and price jumps
// first), leave - and the suppliers' price rises of the last two weeks. Each section shows only what you may decide.
import { api, run } from "/assets/app.js";
import { empty, html, icon, openDialog, pageHead, pill } from "/assets/kit/index.js";
import { head } from "./lib/areas.js";
import { biz } from "./lib/business.js";
import { money } from "./lib/format.js";
import { cash } from "./money/common.js";

async function note(title, needed) {
  const box = document.createElement("div");
  box.innerHTML = String(html`<label>Note${needed ? " (say why)" : " (optional)"}<input name="n"></label>`);
  if (await openDialog({ title, body: box, actions: [{ label: "Back", value: "" }, { label: "OK", value: "ok", primary: true }] }) !== "ok") return null;
  return box.querySelector("input").value;
}

const section = (title, ic, rows, body) => rows.length ? html`<section class="card k-section"><h2>${icon(ic)} ${title} <span class="muted">${rows.length}</span></h2>${rows.map(body)}</section>` : "";

async function approvals(el) {
  const [b, d] = await Promise.all([biz(), api("/approvals")]);
  el.innerHTML = String(html`${pageHead({ ...head("orders"), title: "Approvals", subtitle: d.waiting ? `${d.waiting} waiting for you` : "Nothing waiting" })}
    ${d.waiting || d.rises.length ? "" : empty({ icon: "check", title: "All clear", text: "Orders above your approval amount, bills and leave requests appear here." })}
    ${section("Purchase orders above your amount", "cart", d.orders, (o) => html`<div class="k-row"><a href="#/orders/${o.po_id}"><b>${o.number}</b> ${o.supplier_name}</a>
      <span>${money(b, o.value)} <small class="muted">over ${money(b, o.limit)} · ${o.by}</small></span>
      <span><button class="btn small primary" data-po="${o.po_id}" data-yes="1">Approve</button> <button class="btn small" data-po="${o.po_id}">Reject</button></span></div>`)}
    ${section("Supplier bills to approve", "inbox", d.bills, (x) => html`<div class="k-row"><a href="#/bills/${x.bill_id}"><b>${x.supplier_name}</b> ${x.supplier_ref}</a>
      <span>${cash(x.total)} <small class="muted">due ${x.due}</small> ${x.match === "check" ? pill(`${x.issues} to check`, "bad") : pill(x.match.replace("_", " "), x.match === "matched" ? "good" : "")}
        ${x.jumps ? pill(`${x.jumps} price jump${x.jumps > 1 ? "s" : ""}`, "warn") : ""}</span>
      <span><button class="btn small primary" data-bill="${x.bill_id}" data-check="${x.match === "check" || x.jumps ? 1 : ""}">Approve</button></span></div>`)}
    ${section("Leave requests", "calendar", d.leave, (l) => html`<div class="k-row"><b>${l.name}</b><span>${l.type} · ${l.first} to ${l.last}${l.days ? ` (${l.days} days)` : ""} ${l.note}</span>
      <span><button class="btn small primary" data-leave="${l.leave_id}" data-yes="1">Approve</button> <button class="btn small" data-leave="${l.leave_id}">Decline</button></span></div>`)}
    ${section("Supplier price rises (last 14 days)", "trend", d.rises, (r) => html`<div class="k-row"><b>${r.description}</b><span>${r.supplier_name} · ${r.date}</span>
      <span>${cash(r.from)} → ${cash(r.to)} ${pill(`+${r.pct}%`, r.jump ? "bad" : "warn")}</span></div>`)}`);
  const again = () => approvals(el);
  const on = (sel, fn) => el.querySelectorAll(sel).forEach((x) => x.addEventListener("click", async () => { if (await fn(x)) again(); }));
  on("[data-po]", async (x) => {
    const yes = !!x.dataset.yes, why = await note(yes ? "Approve this order" : "Reject this order", !yes);
    return why !== null && run(() => api(`/orders/${x.dataset.po}/approve`, { method: "POST", body: { approve: yes, note: why } }), yes ? "Approved - it can be sent" : "Rejected");
  });
  on("[data-bill]", async (x) => {
    const why = x.dataset.check ? await note("Approve this bill (it differs from the order or its prices jumped)", true) : "";
    return why !== null && run(() => api(`/bills/${x.dataset.bill}/approve`, { method: "POST", body: { note: why } }), "Approved");
  });
  on("[data-leave]", async (x) => {
    const yes = !!x.dataset.yes, why = yes ? "" : await note("Decline this leave", false);
    return why !== null && run(() => api(`/leave/${x.dataset.leave}/decide`, { method: "POST", body: { approve: yes, note: why } }), yes ? "Approved" : "Declined");
  });
}

export const routes = [
  { path: "/approvals", nav: "Approvals", key: "a", icon: "check", area: "orders", group: "Business", auth: "staff", tenant: true,
    perm: ["manage_business", "payables", "manage_people"], keywords: "approve inbox pending bills leave price", render: approvals },
];
