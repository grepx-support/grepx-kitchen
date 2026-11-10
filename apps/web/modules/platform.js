/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// Platform operator (GrepX): every business on the platform, setting up a new one with its owner's login (Q2),
// and the demo requests from the public page.
import { api, enterSupport, run } from "/assets/app.js";
import { confirm, DataTable, empty, html, icon, kpiRow, pageHead } from "/assets/kit/index.js";
import { area, head } from "./lib/areas.js";
import { stamp } from "./lib/format.js";

async function platform(el) {
  const list = await api("/platform/businesses");
  el.style.setProperty("--area", area("platform"));
  el.innerHTML = String(html`${pageHead({ ...head("platform"), title: "Businesses", subtitle: "Every business on the platform. Each one sees only its own data." })}
    ${kpiRow([{ label: "Businesses", value: list.length, icon: "building", area: area("platform") },
      { label: "Locations", value: list.reduce((a, b) => a + (b.locations || 0), 0), icon: "pin", area: area("stock") }])}
    <div class="grid">${list.map((b) => html`<article class="card accent"><h2>${b.name}</h2><p class="muted">${b.currency} · ${b.timezone}</p><span class="badge">${b.locations} locations</span>
      <div class="row k-section"><button class="btn primary" data-open="${b.id}">${icon("eyeoff", { size: 15 })} Open (read only)</button>
        <button class="btn" data-edit="${b.id}">${icon("settings", { size: 15 })} Open to fix</button></div></article>`)}</div>
    <form class="card accent k-section"><h2>Set up a new business</h2><div class="row"><label>Business name<input name="name" required></label>
        <label>Currency<input name="currency" required maxlength="3" placeholder="AUD"></label><label>Time zone<input name="timezone" required placeholder="Australia/Sydney"></label></div>
      <h2 class="k-section">Owner</h2><div class="row"><label>Name<input name="oname" required></label><label>Email (login)<input name="email" type="email" required></label>
        <label>Phone<input name="phone" required placeholder="+61 412 345 678"></label><label>Password (8+)<input name="password" type="password" minlength="8" required></label></div>
      <p><button class="btn primary">Create business</button></p><p class="muted small">Creates the business, its roles (owner, warehouse, kitchen, closing, delivery) and the owner's login.</p></form>`);
  const open = async (id, edit) => {
    const b = list.find((x) => x.id === id);
    if (edit && !(await confirm({ title: `Change ${b.name}'s data?`, ok: "Open to fix",
      text: "You can change anything in this business for one hour. Every change is saved under your name and the opening is audited." }))) return;
    const s = await run(() => api(`/platform/businesses/${id}/support`, { method: "POST", body: { edit } }));
    if (s) enterSupport(s, s.business_name);
  };
  el.querySelectorAll("[data-open]").forEach((btn) => btn.onclick = () => open(btn.dataset.open, false));
  el.querySelectorAll("[data-edit]").forEach((btn) => btn.onclick = () => open(btn.dataset.edit, true));
  el.querySelector("form").onsubmit = async (e) => {
    e.preventDefault();
    const d = new FormData(e.target);
    if (await run(() => api("/platform/businesses", { method: "POST", body: { name: d.get("name"), currency: d.get("currency"), timezone: d.get("timezone"),
      owner: { name: d.get("oname"), email: d.get("email"), phone: d.get("phone"), password: d.get("password") } } }), "Business created")) platform(el);
  };
}

const STAGES = [["new", "New", "warn"], ["contacted", "Contacted", "info"], ["won", "Won", "good"], ["lost", "Lost", ""]];

async function leads(el) {
  const { leads: list } = await api("/platform/leads");
  el.style.setProperty("--area", area("platform"));
  el.innerHTML = String(html`${pageHead({ ...head("platform"), title: "Demo requests", subtitle: "From the public page. Each one is also emailed to the sales address." })}
    ${kpiRow(STAGES.map(([k, t]) => ({ label: t, value: list.filter((l) => (l.stage || "new") === k).length, icon: k === "won" ? "check" : "user", area: area("platform") })))}
    <section class="card k-section">${list.length ? html`<div class="t"></div>` : empty({ icon: "user", title: "No requests yet", text: "They appear here when someone fills in the form on the public page." })}</section>`);
  if (!list.length) return;
  new DataTable({ rows: list, columns: [
    { key: "created_at", label: "When", render: (l) => html`${stamp(l.created_at)}` },
    { key: "name", label: "Who", render: (l) => html`<b>${l.name}</b><br><span class="muted small">${l.company || ""}${l.size ? ` · ${l.size} locations` : ""}</span>` },
    { key: "email", label: "Contact", render: (l) => html`<a href="mailto:${l.email}">${l.email}</a>${l.phone ? html`<br><span class="small">${l.phone}</span>` : ""}` },
    { key: "message", label: "Message", render: (l) => html`<span class="small">${l.message || ""}</span>` },
    { key: "stage", label: "Stage", render: (l) => html`<select data-lead="${l.id}" aria-label="Stage">${STAGES.map(([k, t]) => html`<option value="${k}" ${(l.stage || "new") === k ? "selected" : ""}>${t}</option>`)}</select>` }] }).mount(el.querySelector(".t"));
  el.querySelector(".t").addEventListener("change", (e) => {
    const id = e.target.dataset?.lead;
    if (id) run(() => api(`/platform/leads/${encodeURIComponent(id)}`, { method: "POST", body: { stage: e.target.value } }), "Saved");
  });
}

export const routes = [
  { path: "/platform", nav: "Businesses", icon: "building", area: "platform", group: "Platform", auth: "admin", platform: true, render: platform },
  { path: "/platform/leads", nav: "Demo requests", icon: "user", area: "platform", group: "Platform", auth: "admin", platform: true, render: leads },
];
