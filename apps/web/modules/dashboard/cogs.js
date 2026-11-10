/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// COGS % and costing % for each count period this month, with the business's target COGS range shaded.
import { api } from "/assets/app.js";
import { html, lineChart } from "/assets/kit/index.js";
import { area } from "../lib/areas.js";
import { has, on } from "../lib/business.js";
import { pct, thisMonth } from "../lib/format.js";

export default {
  id: "cogs", title: "COGS this month", icon: "trend", size: "m", area: area("costs"),
  allowed: ({ b }) => has("view_costs") && on(b, "costing"),
  load: async () => {
    const [d, s] = await Promise.all([api(`/costs/days?month=${thisMonth()}`), api(`/costs/month?month=${thisMonth()}`)]);
    return { days: d.days, s };
  },
  render: ({ days, s }) => days.length ? html`<div class="k-figs"><span><b>${pct(s.cogs_pct)}</b> COGS</span><span><b>${pct(s.costing_pct)}</b> costing avg</span>
      <span class="${s.days_out_of_range ? "bad" : "ok"}"><b>${s.days_out_of_range}</b> day(s) outside ${s.cogs_range[0]}–${s.cogs_range[1]}%</span></div>
    ${lineChart({ labels: days.map((x) => x.date.slice(5)), unit: "%", band: s.cogs_range, label: "COGS by day",
      series: [{ name: "COGS %", color: area("costs"), values: days.map((x) => x.cogs_pct) }, { name: "Costing %", color: "#f59e0b", values: days.map((x) => x.costing_pct) }] })}`
    : html`<p class="muted">No closings this month yet - COGS appears after the first closing.</p>`,
};
