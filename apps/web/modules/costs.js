/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// Daily COGS and costing average, monthly summary (never a profit with a missing cost), one location or all (COS-03..09).
import { api, esc } from "../../app.js";
import { biz, fmt, money } from "./lib.js";

export const routes = [
  { path: "/costs", nav: "Costs", auth: "staff", perm: "view_costs", render: async (el, q) => {
    const b = await biz();
    const month = q.month || new Date().toISOString().slice(0, 7);
    const loc = q.location || "";
    const qs = `month=${month}${loc ? `&location_id=${loc}` : ""}`;
    const [d, s] = await Promise.all([api(`/costs/days?${qs}`), api(`/costs/month?${qs}`)]);
    const pct = (v) => v === null || v === undefined ? "–" : `${fmt(v, 1)}%`;
    el.innerHTML = `<h1>Costs</h1><div class="row"><div><label>Month</label><input type="month" id="m" value="${esc(month)}"></div>
      <div><label>Location</label><select id="l"><option value="">Whole business</option>${b.locations.map((x) => `<option value="${esc(x.id)}" ${x.id === loc ? "selected" : ""}>${esc(x.name)}</option>`).join("")}</select></div></div>
      <div class="grid"><div class="card"><div class="muted">Sales</div><div class="stat">${money(b, s.sales)}</div></div>
        <div class="card"><div class="muted">COGS</div><div class="stat">${pct(s.cogs_pct)}</div><div class="muted small">range ${fmt(s.cogs_range[0])}–${fmt(s.cogs_range[1])}% · ${s.days_out_of_range} day(s) outside</div></div>
        <div class="card"><div class="muted">Costing average</div><div class="stat">${pct(s.costing_pct)}</div></div>
        <div class="card"><div class="muted">Net profit</div><div class="stat ${s.net_profit === null ? "muted" : s.net_profit < 0 ? "bad" : "ok"}">${s.net_profit === null ? "Not yet" : money(b, s.net_profit)}</div>
          ${s.missing.length ? `<div class="bad small">Missing: ${esc(s.missing.join(", "))} - profit is shown when every cost is in.</div>` : ""}</div></div><br>
      <div class="card"><h2>Month</h2><table><tr><td>Sales</td><td>${money(b, s.sales)}</td></tr><tr><td>Ingredient cost</td><td>${money(b, s.ingredient_cost)}</td></tr>
        <tr><td colspan="2" class="muted small">Labour, rent and other: ${esc(s.overheads_days)} day(s) of the month</td></tr><tr><td>Labour</td><td>${money(b, s.labour)}</td></tr><tr><td>Rent</td><td>${money(b, s.rent)}</td></tr><tr><td>Other costs</td><td>${money(b, s.other)}</td></tr>
        <tr><th>Net profit</th><th>${s.net_profit === null ? "–" : money(b, s.net_profit)}</th></tr></table></div><br>
      <div class="card"><h2>Each count period</h2><table><tr><th>Day</th><th>Location</th><th>Sales</th><th>Ingredients</th><th>COGS</th><th>Costing</th></tr>
        ${d.days.map((x) => `<tr class="${x.out_of_range ? "bad" : ""}"><td>${esc(x.date)}${x.period_days > 1 ? ` <span class="muted small">(${x.period_days} days)</span>` : ""}</td><td>${esc(x.location_name)}</td>
          <td>${fmt(x.sales)}</td><td>${fmt(x.ingredient_cost)}</td><td>${pct(x.cogs_pct)}${x.out_of_range ? " ⚠" : ""}</td><td>${pct(x.costing_pct)}</td></tr>`).join("") || '<tr><td colspan="6" class="muted">No closings this month.</td></tr>'}</table></div>`;
    const go = () => { location.hash = `#/costs?month=${el.querySelector("#m").value}&location=${el.querySelector("#l").value}`; };
    el.querySelector("#m").onchange = go; el.querySelector("#l").onchange = go;
  } },
];
