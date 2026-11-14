/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// Monthly costs per place, in full: every cost line (salaries, rent, utilities, delivery-app commission, your own),
// grouped into staff, premises and running costs. Six months side by side with the change on the month before; click
// a cell to edit that place's month. Share a cost paid for several places; start a month from the last one. The
// three group totals are spread over the days of the month in the daily costing (COS-07).
import { api } from "/assets/app.js";
import { barList, columnChart, html, icon, kpiRow } from "/assets/kit/index.js";
import { fmt, thisMonth } from "../lib/format.js";
import { post } from "./common.js";
import { editCosts } from "./overhead-editor.js";
import { shareCost } from "./overhead-share.js";

const prev = (m) => { const [y, n] = m.split("-").map(Number); return n === 1 ? `${y - 1}-12` : `${y}-${String(n - 1).padStart(2, "0")}`; };
const change = (c) => (c == null ? "" : html`<small class="${c > 0 ? "bad" : "ok"}">${c > 0 ? "+" : ""}${c}%</small>`);

export default {
  id: "costs", label: "Monthly costs", icon: "coin",
  async render(el, s, q, { redraw }) {
    const month = q.month || thisMonth();
    const d = await api(`/setup/overheads?month=${month}&months=6`);
    const places = s.locations.filter((l) => l.active !== false);
    const now = d.per_month.at(-1), before = d.per_month.at(-2);
    const cell = (pid, m) => d.cells.find((c) => c.location_id === pid && c.month === m);
    el.innerHTML = String(html`<div class="row oh-bar"><label>Month<input type="month" name="month" value="${month}"></label>
        <button class="btn" data-copy>${icon("copy", { size: 15 })} Copy ${prev(month)} into ${month}</button>
        <button class="btn" data-share>${icon("users", { size: 15 })} Share a cost</button></div>
      ${kpiRow([...Object.entries(d.groups).map(([g, label]) => ({ label, value: fmt(now[g]), icon: g === "labour" ? "users" : g === "rent" ? "store" : "bolt", area: g === "labour" ? "#7c3aed" : g === "rent" ? "#0ea5e9" : "#f59e0b",
          note: before && before[g] ? `${fmt(before[g])} in ${before.month}` : "" })),
        { label: "Total this month", value: fmt(now.total), icon: "coin", area: "#16a34a", note: before?.total ? `${Math.round((now.total - before.total) / before.total * 1000) / 10}% on ${before.month}` : "" }])}
      <section class="card k-section"><h2>${icon("calendar")} Place by month <span class="muted small">click a cell to enter or change its costs</span></h2>
        <div class="oh-scroll"><table class="m-view oh-grid"><thead><tr><th>Place</th>${d.months.map((m) => html`<th class="end">${m}</th>`)}</tr></thead><tbody>
        ${places.map((p) => html`<tr><td><b>${p.name}</b></td>${d.months.map((m) => { const c = cell(p.id, m);
          return html`<td class="end oh-cell ${c?.total == null ? "empty" : ""}" data-place="${p.id}" data-month="${m}" title="${c?.lines.map((l) => `${l.category}: ${fmt(l.amount)}`).join("\n") || "Nothing yet - click to enter"}">
            ${c?.total == null ? html`<span class="muted">+ add</span>` : html`${fmt(c.total)}<br>${change(c.change_pct)}${c.shared ? html` <small class="muted">incl. ${fmt(c.shared)} shared</small>` : ""}`}</td>`; })}</tr>`)}
        <tr class="oh-sum"><td>All places</td>${d.per_month.map((m) => html`<td class="end"><b>${fmt(m.total)}</b></td>`)}</tr></tbody></table></div></section>
      <div class="grid two"><section class="card"><h2>${icon("chart")} Total by month</h2>${columnChart({ labels: d.months.map((m) => m.slice(2)), values: d.per_month.map((m) => m.total), color: "#f59e0b", label: "Costs by month" })}</section>
        <section class="card"><h2>${icon("list")} ${month} by cost</h2>${barList({ rows: d.by_category.map((c) => ({ label: `${c.category} · ${d.groups[c.group]}`, value: c.amount })), empty: "No costs entered for this month." })}</section></div>`);
    el.querySelector("[name=month]").onchange = (e) => redraw({ month: e.target.value });
    el.querySelector("[data-copy]").onclick = async () => { if (await post("/setup/overheads/copy", { from_month: prev(month), to_month: month }, "Copied")) redraw({ month }); };
    el.querySelector("[data-share]").onclick = async () => { if (await shareCost({ places, month, groups: d.groups, categories: d.categories })) redraw({ month }); };
    el.querySelector(".oh-grid").addEventListener("click", async (e) => {
      const td = e.target.closest("[data-place]");
      if (!td) return;
      const place = places.find((p) => p.id === td.dataset.place);
      if (await editCosts({ place, month: td.dataset.month, lines: cell(place.id, td.dataset.month)?.lines || [], categories: d.categories, groups: d.groups })) redraw({ month });
    });
  },
};
