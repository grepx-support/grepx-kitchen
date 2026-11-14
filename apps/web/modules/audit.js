/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// Audit trail: every change anyone made in the business - who, when, what, done or refused and why. Filter by days,
// area, person and refused; open a line for all its details; download as CSV.
import { api } from "/assets/app.js";
import { DataTable, empty, html, icon, kpiRow, openDialog, pageHead, pill } from "/assets/kit/index.js";
import { area, head } from "./lib/areas.js";
import { downloadCsv } from "./lib/csv.js";
import { stamp } from "./lib/format.js";
import { showDetails } from "./lib/details.js";

const DAYS = [1, 7, 30, 90];
const link = (q, extra) => `#/audit?${new URLSearchParams(Object.entries({ ...q, ...extra }).filter(([, v]) => v !== "" && v != null))}`;

function details(e) {
  const rows = Object.entries(e.fields).map(([k, v]) => html`<tr><th>${k.replace(/_/g, " ")}</th><td>${typeof v === "object" ? JSON.stringify(v) : String(v)}</td></tr>`);
  openDialog({ title: `${e.action} - ${e.area}`, wide: true, body: html`<p class="muted small">${e.who} · ${stamp(e.at)} ·
    ${e.done ? "done" : html`<b class="bad">refused: ${e.why}</b>`}</p><table class="kit-table au-fields">${rows}</table>` });
}

async function audit(el, q) {
  const { entries, more } = await api(`/audit?days=${q.days || 7}`);
  const shown = entries.filter((e) => (!q.area || e.area === q.area) && (!q.who || e.who === q.who) && (!q.refused || !e.done));
  const areas = [...new Set(entries.map((e) => e.area))].sort(), people = [...new Set(entries.map((e) => e.who))].sort();
  el.style.setProperty("--area", area("setup"));
  el.innerHTML = String(html`${pageHead({ ...head("setup"), title: "Audit trail", subtitle: "Who changed what, and when - nothing changes without a line here.",
    actions: html`<button class="btn" data-csv>${icon("download", { size: 16 })} CSV</button>` })}
    ${kpiRow([{ label: "Changes", value: entries.length, icon: "clipboard", area: "#475569" },
      { label: "People", value: people.length, icon: "users", area: "#2563eb" },
      { label: "Refused", value: entries.filter((e) => !e.done).length, icon: "alert", area: "#e11d48", href: link(q, { refused: 1 }) },
      { label: "Areas", value: areas.length, icon: "layout", area: "#7c3aed" }])}
    <div class="au-bar"><div class="kit-chips">${DAYS.map((d) => html`<a class="kit-chip ${Number(q.days || 7) === d ? "on" : ""}" href="${link(q, { days: d })}">${d === 1 ? "Today" : `${d} days`}</a>`)}</div>
      <select data-f="area"><option value="">Every area</option>${areas.map((a) => html`<option ${q.area === a ? "selected" : ""}>${a}</option>`)}</select>
      <select data-f="who"><option value="">Everyone</option>${people.map((p) => html`<option ${q.who === p ? "selected" : ""}>${p}</option>`)}</select>
      <label class="check"><input type="checkbox" data-f="refused" ${q.refused ? "checked" : ""}> Refused only</label>
      ${more ? html`<span class="muted small">Showing the newest 3,000 - pick fewer days for the rest.</span>` : ""}</div>
    <section class="card k-section">${shown.length ? html`<div class="t"></div>` : empty({ icon: "clipboard", title: "Nothing in this view", text: "Try more days or another filter." })}</section>`);
  el.querySelectorAll("[data-f]").forEach((f) => f.addEventListener("change", () => {
    location.hash = link(q, { [f.dataset.f]: f.type === "checkbox" ? (f.checked ? 1 : "") : f.value });
  }));
  el.querySelector("[data-csv]").addEventListener("click", () => downloadCsv(`audit-${q.days || 7}-days.csv`,
    [["When", "Who", "Area", "Change", "Details", "Done", "Why refused"], ...shown.map((e) => [e.at, e.who, e.area, e.action, e.what, e.done ? "yes" : "no", e.why])]));
  if (!shown.length) return;
  new DataTable({ onRow: (r) => showDetails(`${r.action || "Change"} - ${r.at || ""}`, r), rows: shown, columns: [
    { key: "at", label: "When", render: (e) => html`${stamp(e.at)}` },
    { key: "who", label: "Who" },
    { key: "area", label: "Area", render: (e) => html`${pill(e.area, "")}` },
    { key: "action", label: "Change", render: (e) => html`<a href="javascript:void 0" data-open="${e.id}">${e.action}</a>` },
    { key: "what", label: "Details", render: (e) => html`<span class="muted small">${e.what}</span>` },
    { key: "done", label: "", render: (e) => html`${e.done ? pill("done", "good") : pill("refused", "bad")}` }] }).mount(el.querySelector(".t"));
  el.querySelector(".t").addEventListener("click", (ev) => {
    const e = shown.find((x) => x.id === ev.target.closest("[data-open]")?.dataset.open);
    if (e) { ev.preventDefault(); details(e); }
  });
}

export const routes = [
  { path: "/audit", nav: "Audit trail", icon: "clipboard", area: "setup", group: "Setup", auth: "staff", tenant: true, perm: "manage_business", render: audit,
    keywords: "audit log history who changed activity trail compliance" },
];
