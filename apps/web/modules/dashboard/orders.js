/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// Purchase orders waiting to arrive.
import { api } from "/assets/app.js";
import { html, pill } from "/assets/kit/index.js";
import { area } from "../lib/areas.js";
import { has, on } from "../lib/business.js";

export default {
  id: "open-orders", title: "Orders on the way", icon: "cart", area: area("orders"), href: "#/orders",
  allowed: ({ b }) => (has("orders") || has("warehouse_in")) && on(b, "orders"),
  load: () => api("/orders?state=saved"),
  render: (d) => html`<p class="k-big">${d.orders.length}<small> open</small></p>${d.orders.slice(0, 4).map((o) => html`<a class="k-row" href="#/orders/${o.id}">
      <b>${o.number}</b><span>${o.supplier_name || ""}</span>${pill(`${o.lines.length} lines`, "info")}</a>`)}
    ${d.orders.length ? "" : html`<p class="muted">Nothing waiting.</p>`}`,
};
