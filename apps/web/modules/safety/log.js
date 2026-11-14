/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// The food safety log for inspectors: every record between two dates at one place or all, who and when, failures
// with the action taken - print it or download it.
import { api } from "/assets/app.js";
import { DataTable, html, icon, kpiRow, pageHead, pill, tabs } from "/assets/kit/index.js";
import { area, head } from "../lib/areas.js";
import { biz } from "../lib/business.js";
import { downloadCsv } from "../lib/csv.js";
import { TABS } from "./today.js";
import { openPdf } from "../money/common.js";

export async function logPage(el, q) {
  const b = await biz();
  const last = q.last || new Date().toISOString().slice(0, 10), first = q.first || new Date(Date.now() - 29 * 864e5).toISOString().slice(0, 10);
  const h = await api(`/safety/history?first=${first}&last=${last}&site_id=${q.site || ""}`);
  const place = (id) => b.locations.find((l) => l.id === id)?.name || "";
  el.style.setProperty("--area", area("safety"));
  el.innerHTML = String(html`${pageHead({ ...head("safety"), title: "Food safety log", subtitle: `${first} to ${last}${q.site ? ` · ${place(q.site)}` : " · every place"}`,
    actions: html`<form class="row sf-range"><input type="date" name="first" value="${first}"><input type="date" name="last" value="${last}"><select name="site"><option value="">Every place</option>${b.locations.map((l) =>
      html`<option value="${l.id}" ${q.site === l.id ? "selected" : ""}>${l.name}</option>`)}</select><button class="btn">Show</button></form>
      <button class="btn" data-csv>${icon("download", { size: 15 })} CSV</button><button class="btn" data-pdf>${icon("printer", { size: 15 })} PDF</button>` })}
    ${tabs(TABS, "log")}${kpiRow([{ label: "Records", value: h.total, icon: "clipboard", area: area("safety") },
      { label: "Out of range", value: h.failed, icon: "alert", area: h.failed ? "#e11d48" : "#94a3b8" },
      { label: "In range", value: h.total ? `${Math.round((1 - h.failed / h.total) * 100)}%` : "-", icon: "check", area: "#16a34a" }])}
    <section class="card k-section"><div class="t"></div></section>`);
  el.querySelector(".sf-range").onsubmit = (e) => { e.preventDefault(); location.hash = `#/safety/log?${new URLSearchParams(new FormData(e.target))}`; };
  el.querySelector("[data-pdf]").onclick = () => openPdf(`/pdf/safety?first=${first}&last=${last}&site_id=${q.site || ""}`);
  el.querySelector("[data-csv]").onclick = () => downloadCsv(`food-safety-${first}-${last}.csv`, [["When", "Place", "Check", "Value", "In range", "Action taken", "By"],
    ...h.records.map((r) => [r.at, place(r.site_id), r.point_name, r.value ?? (r.failed || []).join("; "), r.ok ? "yes" : "no", r.action_taken, r.by])]);
  new DataTable({ rows: h.records, columns: [
    { key: "at", label: "When", render: (r) => html`${r.at.replace("T", " ")}` }, { key: "site_id", label: "Place", render: (r) => html`${place(r.site_id)}` },
    { key: "point_name", label: "Check" }, { key: "value", label: "Reading", render: (r) => html`${r.value != null ? `${r.value}${r.unit}` : (r.failed || []).join(", ") || "all yes"}` },
    { key: "ok", label: "", render: (r) => html`${r.ok ? pill("in range", "good") : pill("out", "bad")}` },
    { key: "action_taken", label: "Action taken" }, { key: "by", label: "By" }] }).mount(el.querySelector(".t"));
}
