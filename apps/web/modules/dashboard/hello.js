/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// Greeting with the date and one-tap tiles for this user's daily jobs (QR-02: no help needed).
import { state } from "/assets/app.js";
import { html, icon } from "/assets/kit/index.js";
import { area, areaIcon } from "../lib/areas.js";
import { has, on } from "../lib/business.js";
import { greeting } from "../lib/format.js";

const JOBS = [
  { perm: "kitchen", module: "kitchen", href: "#/kitchen", area: "kitchen", title: "Kitchen", text: "Target, production, ingredients" },
  { perm: "closing", module: "closing", href: "#/closing", area: "closing", title: "Closing", text: "Count, sales, issues" },
  { perm: "warehouse_out", module: "inventory", href: "#/stock/out", area: "out", title: "Warehouse out", text: "Send stock out" },
  { perm: "warehouse_in", module: "inventory", href: "#/stock/in", area: "in", title: "Warehouse in", text: "Receive deliveries" },
  { perm: "orders", module: "orders", href: "#/orders", area: "orders", title: "Orders", text: "Reorder and purchase orders" },
  { perm: "delivery", module: "inventory", href: "#/stock/deliveries", area: "deliveries", title: "Deliveries", text: "What leaves the warehouse" },
  { perm: "transfer", module: "inventory", href: "#/stock/move", area: "move", title: "Transfer", text: "Move or correct stock" },
  { perm: "view_costs", module: "costing", href: "#/costs", area: "costs", title: "Costs", text: "COGS and profit" },
];

export default {
  id: "hello", title: "Today", icon: "sparkle", size: "l", area: "var(--primary)",
  load: async ({ b }) => JOBS.filter((j) => has(j.perm) && on(b, j.module)),
  render: (jobs, { b }) => html`<div class="k-hello"><div><p class="k-date">${new Date().toLocaleDateString(undefined, { weekday: "long", day: "numeric", month: "long" })}</p>
      <h2>${greeting()}, ${(state.me?.name || "").split(" ")[0]}</h2><p class="muted">${b.business?.name || ""} · ${b.locations?.length || 0} locations</p></div>
    <div class="k-jobs">${jobs.map((j) => html`<a class="k-job" href="${j.href}" style="--area:${area(j.area)}"><span>${icon(areaIcon(j.area), { size: 22 })}</span>
      <b>${j.title}</b><small>${j.text}</small></a>`)}${jobs.length ? "" : html`<p class="muted">Your account has no tasks yet - ask your owner for a role.</p>`}</div></div>`,
};
