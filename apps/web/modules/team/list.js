/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// Team -> People: everyone across the outlets (or one outlet), position, outlets, documents running out; add someone.
import { api } from "/assets/app.js";
import { DataTable, empty, html, icon, kpiRow, pill } from "/assets/kit/index.js";
import { biz } from "../lib/business.js";
import { frame, siteName } from "./common.js";

const DOC = { expired: "bad", expiring: "warn", valid: "good", no_expiry: "" };

export async function teamPage(el, q) {
  const b = await biz();
  const t = await api(`/team?site_id=${q.site || ""}`);
  const active = t.team.filter((p) => p.active !== false);
  const body = frame(el, "people", "Team", "Everyone across your outlets - documents, outlets, pay basis.",
    html`<a class="btn primary" href="#/team/person">${icon("plus", { size: 16 })} Add a person</a>`);
  body.innerHTML = String(html`${kpiRow([{ label: "People", value: active.length, icon: "users", area: "#0891b2" },
      { label: "Outlets", value: b.locations.length, icon: "store", area: "#7c3aed" },
      { label: "Documents to renew", value: t.documents_due.length, icon: "alert", area: t.documents_due.length ? "#e11d48" : "#94a3b8" },
      { label: "Left", value: t.team.length - active.length, icon: "logout", area: "#64748b" }])}
    <div class="kit-chips"><a class="kit-chip ${q.site ? "" : "on"}" href="#/team">All outlets</a>${b.locations.map((l) =>
      html`<a class="kit-chip ${q.site === l.id ? "on" : ""}" href="#/team?site=${l.id}">${l.name}</a>`)}</div>
    ${t.documents_due.length ? html`<section class="card tm-due">${icon("alert")} ${t.documents_due.map((d) =>
      html`<a href="#/team/person?id=${d.employee_id}">${pill(`${d.name}: ${d.kind} ${d.state} ${d.expires_on}`, DOC[d.state])}</a>`)}</section>` : ""}
    <section class="card k-section">${t.team.length ? html`<div class="t"></div>` : empty({ icon: "users", title: "Nobody yet", text: "Add your chefs, cooks and outlet staff." })}</section>`);
  if (!t.team.length) return;
  new DataTable({ onRow: (p) => { location.hash = `#/team/person?id=${p.employee_id}`; }, rows: t.team, columns: [
    { key: "name", label: "Name", render: (p) => html`<a href="#/team/person?id=${p.employee_id}"><b>${p.name}</b></a>${p.active === false ? html` ${pill("left", "")}` : ""}` },
    { key: "position", label: "Position" },
    { key: "home_site", label: "Home outlet", render: (p) => html`${siteName(b, p.home_site)}` },
    { key: "sites", label: "Also works at", render: (p) => html`<span class="muted small">${p.sites.filter((s) => s !== p.home_site).map((s) => siteName(b, s)).join(", ")}</span>` },
    { key: "phone", label: "Phone" },
    { key: "docs", label: "Documents", render: (p) => html`${p.documents.map((d) => pill(d.kind, DOC[d.state]))}` }] }).mount(body.querySelector(".t"));
}
