/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// What the holding place needs for the coming week (beyond stock already held) - the shopping signal.
import { api } from "/assets/app.js";
import { barList, html } from "/assets/kit/index.js";
import { area } from "../lib/areas.js";
import { has, on } from "../lib/business.js";
import { fmt } from "../lib/format.js";

export default {
  id: "needed", title: "Needed this week", icon: "alert", area: area("in"),
  allowed: ({ b }) => has("warehouse_in") && on(b, "inventory") && b.locations.some((l) => l.holding),
  load: ({ b }) => api(`/stock/warehouse-in?location_id=${b.locations.find((l) => l.holding).id}`),
  render: (d) => {
    const rows = d.lines.filter((l) => l.needed > 0).sort((a, z) => z.needed - a.needed).slice(0, 6);
    return rows.length ? html`${barList({ rows: rows.map((l) => ({ label: l.name, value: l.needed, marker: l.weekly_usage, note: `have ${fmt(l.at_holding)} ${l.unit}`, color: "#f43f5e" })) })}
      <p><a class="btn small" href="#/orders">Order now</a></p>` : html`<p class="ok">Nothing needed - stock covers the week.</p>`;
  },
};
