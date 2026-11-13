/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// Which locations have closed today, and the latest closings with their sales and issues.
import { api } from "/assets/app.js";
import { html } from "/assets/kit/index.js";
import { area } from "../lib/areas.js";
import { has, on } from "../lib/business.js";
import { fmt, today } from "../lib/format.js";

export default {
  id: "closings", title: "Closings", icon: "clipboard", area: area("closing"), href: "#/closing",
  allowed: ({ b }) => (has("manage_business") || has("view_costs")) && on(b, "closing"),
  load: () => api("/closing/history"),
  render: (d, { b }) => {
    const done = new Set(d.closings.filter((c) => c.date === today()).map((c) => c.location_id));
    const sells = b.locations.filter((l) => !l.holding || l.kind !== "warehouse");
    return html`<div class="k-dots">${sells.map((l) => html`<span class="${done.has(l.id) ? "on" : ""}" title="${l.name}">${l.name}</span>`)}</div>
      ${d.closings.slice(0, 3).map((c) => html`<div class="k-row"><b>${c.date.slice(5)}</b><span>${c.location_name} · ${c.staff_name}</span><span>${fmt(c.total_sales, 0)}</span></div>
        ${c.issues ? html`<p class="k-issue">⚠ ${c.issues}</p>` : ""}`)}${d.closings.length ? "" : html`<p class="muted">No closings yet.</p>`}`;
  },
};
