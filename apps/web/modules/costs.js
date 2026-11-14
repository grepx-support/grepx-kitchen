/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// Daily COGS and costing average, monthly summary (never a profit with a missing cost), one location or all (COS-03..09).
import { api } from "/assets/app.js";
import { barList, DataTable, html, icon, kpiRow, pageHead } from "/assets/kit/index.js";
import { area, head } from "./lib/areas.js";
import { biz } from "./lib/business.js";
import { byDay } from "./lib/days.js";
import { fmt, money, pct, thisMonth } from "./lib/format.js";
import * as chart from "./costs/charts.js";
import { costLandscape } from "./costs/view3d.js";

async function costs(el, q) {
  const b = await biz();
  const day = /^\d{4}-\d{2}-\d{2}$/.test(q.day || "") ? q.day : "";      // a day picked in a chart: its month, its rows
  const month = day ? day.slice(0, 7) : q.month || thisMonth();
  const loc = q.location || "";
  const qs = `month=${month}${loc ? `&location_id=${loc}` : ""}`;
  const [d, s] = await Promise.all([api(`/costs/days?${qs}`), api(`/costs/month?${qs}`)]);
  el.style.setProperty("--area", area("costs"));
  const daily = byDay(d.days);
  const profitTone = s.net_profit === null ? "" : s.net_profit < 0 ? "bad" : "good";
  el.innerHTML = String(html`${pageHead({ ...head("costs"), title: "Costs", subtitle: "Ingredient cost against sales, and what is left after labour and rent.",
      actions: html`<label class="pick">Month<input type="month" id="m" value="${month}"></label><label class="pick">Location<select id="l"><option value="">Whole business</option>
        ${b.locations.map((x) => html`<option value="${x.id}" ${x.id === loc ? "selected" : ""}>${x.name}</option>`)}</select></label>` })}
    ${kpiRow([{ label: "Sales", value: money(b, s.sales), icon: "coin", area: "#0ea5e9", trend: daily.map((x) => x.sales) },
      { label: "COGS", value: pct(s.cogs_pct), icon: "trend", area: area("costs"), note: `target ${s.cogs_range[0]}–${s.cogs_range[1]}% · ${s.days_out_of_range} day(s) outside`,
        tone: s.days_out_of_range ? "bad" : "good", trend: daily.map((x) => x.cogs_pct) },
      { label: "Costing average", value: pct(s.costing_pct), icon: "chart", area: "#f59e0b", trend: daily.map((x) => x.costing_pct) },
      { label: "Net profit", value: s.net_profit === null ? "Not yet" : money(b, s.net_profit), icon: "sparkle", area: "#16a34a", tone: profitTone, note: `${s.overheads_days} day(s) of overheads` }])}
    ${chart.missing(s)}
    <section class="card k-section c3" data-landscape></section>
    <div class="grid two"><section class="card accent"><h2>${icon("trend")} COGS by count period</h2>${d.days.length ? chart.trend(d.days, s) : html`<p class="muted">No closings this month.</p>`}</section>
      <section class="card accent"><h2>${icon("coin")} Where the money went</h2>${chart.split(s, b)}</section></div>
    ${s.cost_lines?.length ? html`<section class="card k-section"><h2>${icon("list")} Costs this month, line by line <a class="small" href="#/setup?tab=costs">change</a></h2>
      ${barList({ rows: s.cost_lines.map((c) => ({ label: c.category, value: c.amount })) })}</section>` : ""}
    <section class="card accent k-section"><h2>${icon("chart")} Sales by count period</h2>${d.days.length ? chart.sales(d.days) : html`<p class="muted">No sales yet.</p>`}</section>
    <section class="card k-section" id="days"><h2>Each count period ${day ? html`<a class="kit-chip on" href="#/costs?month=${month}${loc ? `&location=${loc}` : ""}" title="Show the whole month">${day} ✕</a>` : ""}</h2><div class="days"></div></section>`);
  costLandscape(el.querySelector("[data-landscape]"), d.days, { ...s, cogs_range: d.cogs_range?.[0] != null ? d.cogs_range : s.cogs_range }, b.business?.currency || d.currency || "");
  new DataTable({ onRow: (r) => { location.hash = `#/costs?day=${r.date}`; }, rows: day ? d.days.filter((x) => x.date === day) : d.days, empty: day ? "No closing on this day." : "No closings this month.", columns: [
    { key: "date", label: "Day", render: (x) => html`${x.date}${x.period_days > 1 ? html` <span class="muted small">(${x.period_days} days)</span>` : ""}` },
    { key: "location_name", label: "Location" },
    { key: "sales", label: "Sales", align: "end", render: (x) => html`${fmt(x.sales)}` },
    { key: "ingredient_cost", label: "Ingredients", align: "end", render: (x) => html`${fmt(x.ingredient_cost)}` },
    { key: "cogs_pct", label: "COGS", align: "end", render: (x) => html`<b class="${x.out_of_range ? "bad" : "ok"}">${pct(x.cogs_pct)}${x.out_of_range ? " ⚠" : ""}</b>` },
    { key: "costing_pct", label: "Costing", align: "end", render: (x) => html`${pct(x.costing_pct)}` }] }).mount(el.querySelector(".days"));
  const go = () => { location.hash = `#/costs?month=${el.querySelector("#m").value}&location=${el.querySelector("#l").value}`; };
  el.querySelector("#m").onchange = go;
  el.querySelector("#l").onchange = go;
  if (day) el.querySelector("#days").scrollIntoView({ behavior: "smooth", block: "start" });
}

export const routes = [
  { path: "/costs", nav: "Costs", key: "m", icon: "chart", area: "costs", group: "Money", auth: "staff", tenant: true, perm: "view_costs", render: costs },
];
