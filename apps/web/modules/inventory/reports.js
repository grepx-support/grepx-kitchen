/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// Valuation (what the stock is worth, by location) and analysis (ABC by usage value, days of cover, waste by reason).
import { api } from "/assets/app.js";
import { barList, DataTable, donut, html, icon, kpiRow, pill } from "/assets/kit/index.js";
import { biz } from "../lib/business.js";
import { fmt, money } from "../lib/format.js";
import { REASONS } from "../lib/waste.js";
import { frame } from "./common.js";

export async function value(el) {
  const [b, v] = await Promise.all([biz(), api("/inventory/valuation")]);
  const body = frame(el, "value", "On hand at today's cost, and by the cost of each lot where lots carry one.");
  const byPlace = {};
  v.lines.forEach((l) => { byPlace[l.location_name] = (byPlace[l.location_name] || 0) + l.value; });
  body.innerHTML = String(html`${kpiRow([{ label: "Stock value", value: money(b, v.total), icon: "coin", area: "#16a34a" },
      { label: "By lot cost", value: money(b, v.lot_total), icon: "box", area: "#0ea5e9", note: "first in, first out" },
      { label: "Lines", value: v.lines.length, icon: "list", area: "#8b5cf6" }])}
    <div class="grid two"><section class="card accent"><h2>${icon("pin")} By location</h2>${barList({ rows: Object.entries(byPlace).sort((a, z) => z[1] - a[1]).map(([k, n]) => ({ label: k, value: n, color: "#16a34a" })) })}</section>
      <section class="card"><h2>Every line</h2><div class="t"></div></section></div>`);
  new DataTable({ rows: v.lines, columns: [{ key: "name", label: "Item" }, { key: "location_name", label: "Location" },
    { key: "qty", label: "Qty", align: "end", render: (l) => html`${fmt(l.qty)} ${l.unit}` },
    { key: "value", label: "Value", align: "end", render: (l) => html`${money(b, l.value)}` }] }).mount(body.querySelector(".t"));
}

const CLASS = { A: ["#e11d48", "the few that carry most of the cost: count often, never run out"], B: ["#f59e0b", "middle"], C: ["#16a34a", "many items, little value"] };

export async function analysis(el, q) {
  const [b, a] = await Promise.all([biz(), api(`/inventory/analysis?days=${q.days || 30}`)]);
  const body = frame(el, "analysis", `Last ${a.days} days, since ${a.since}.`,
    html`<div class="kit-chips">${[14, 30, 60, 90].map((n) => html`<a class="kit-chip ${n === a.days ? "on" : ""}" href="#/inventory/analysis?days=${n}">${n} days</a>`)}</div>`);
  const count = (c) => a.items.filter((i) => i.class === c && i.used_value > 0).length;
  const low = a.items.filter((i) => i.days_of_cover !== null && i.days_of_cover < 3);
  const wasted = Object.values(a.waste).reduce((x, y) => x + y, 0);
  body.innerHTML = String(html`${kpiRow([{ label: "A items", value: count("A"), icon: "alert", area: CLASS.A[0], note: "80% of usage value" },
      { label: "Less than 3 days of cover", value: low.length, icon: "clock", area: "#f59e0b", tone: low.length ? "bad" : "good" },
      { label: "Waste", value: money(b, wasted), icon: "x", area: "#64748b" }])}
    <div class="grid two"><section class="card accent"><h2>${icon("chart")} ABC by usage value</h2>${donut({ centre: String(a.items.filter((i) => i.used_value > 0).length), caption: "items used",
        parts: ["A", "B", "C"].map((c) => ({ label: `${c} - ${CLASS[c][1]}`, value: count(c), color: CLASS[c][0] })) })}</section>
      <section class="card accent"><h2>${icon("x")} Waste by reason</h2>${wasted ? donut({ centre: fmt(wasted, 0), caption: b.business?.currency || "",
        parts: REASONS.map(([k, t], n) => ({ label: t, value: a.waste[k] || 0, color: ["#e11d48", "#f97316", "#8b5cf6", "#0ea5e9", "#94a3b8"][n] })) }) : html`<p class="muted">No waste recorded.</p>`}</section></div>
    <section class="card k-section"><h2>Items</h2><div class="t"></div></section>`);
  new DataTable({ rows: a.items, columns: [{ key: "name", label: "Item" }, { key: "class", label: "Class", render: (i) => html`${pill(i.class, i.class === "A" ? "bad" : i.class === "B" ? "warn" : "good")}` },
    { key: "used_value", label: "Used (value)", align: "end", render: (i) => html`${money(b, i.used_value)}` },
    { key: "used_qty", label: "Used", align: "end", render: (i) => html`${fmt(i.used_qty)} ${i.unit}` },
    { key: "on_hand", label: "On hand", align: "end", render: (i) => html`${fmt(i.on_hand)}` },
    { key: "days_of_cover", label: "Days of cover", align: "end", value: (i) => i.days_of_cover ?? 9999,
      render: (i) => html`<b class="${i.days_of_cover !== null && i.days_of_cover < 3 ? "bad" : ""}">${i.days_of_cover ?? "–"}</b>` }] }).mount(body.querySelector(".t"));
}
