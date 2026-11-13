/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// Today's warehouse-out trips: how many are still on the way and how many arrived.
import { api } from "/assets/app.js";
import { html, progress } from "/assets/kit/index.js";
import { area } from "../lib/areas.js";
import { has, on } from "../lib/business.js";
import { time, today } from "../lib/format.js";

export default {
  id: "deliveries", title: "Deliveries today", icon: "truck", area: area("deliveries"), href: "#/stock/deliveries",
  allowed: ({ b }) => (has("delivery") || has("warehouse_out")) && on(b, "inventory"),
  load: () => api(`/stock/deliveries?date=${today()}`),
  render: (d) => {
    const done = d.deliveries.filter((t) => t.state === "delivered").length;
    return html`<p class="k-big">${d.deliveries.length}<small> trips</small></p>${d.deliveries.length ? progress(done, d.deliveries.length, { label: "Delivered" }) : ""}
      ${d.deliveries.slice(0, 4).map((t) => html`<a class="k-row" href="#/stock/deliveries"><b>${time(t.at)}</b><span>→ ${t.to}</span>
        <span class="kit-pill ${t.state === "delivered" ? "good" : "warn"}">${t.state}</span></a>`)}
      ${d.deliveries.length ? "" : html`<p class="muted">Nothing sent today.</p>`}`;
  },
};
