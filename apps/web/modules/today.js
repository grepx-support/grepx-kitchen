/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// Home: what this user does today, by role - one tap to each daily task (QR-02: no help needed).
import { api, esc, state } from "../../app.js";
import { biz, has, on } from "./lib.js";

const TILES = [
  { perm: "kitchen", module: "kitchen", href: "#/kitchen", title: "Kitchen", text: "This week's target, record production and ingredients" },
  { perm: "closing", module: "closing", href: "#/closing", title: "Staff closing", text: "Count stock, note issues, enter sales" },
  { perm: "warehouse_out", module: "inventory", href: "#/stock/out", title: "Warehouse out", text: "Send stock to each location" },
  { perm: "warehouse_in", module: "inventory", href: "#/stock/in", title: "Warehouse in", text: "Receive deliveries and orders" },
  { perm: "orders", module: "orders", href: "#/orders", title: "Orders", text: "Reorder recommendation and purchase orders" },
  { perm: "transfer", module: "inventory", href: "#/stock/move", title: "Transfer / adjust", text: "Move stock between stores, fix counts" },
  { perm: "view_stock", module: "inventory", href: "#/stock", title: "Stock", text: "Stock at every location and its history" },
  { perm: "delivery", module: "inventory", href: "#/stock/deliveries", title: "Deliveries", text: "What leaves the warehouse" },
  { perm: "view_costs", module: "costing", href: "#/costs", title: "Costs", text: "Daily COGS, costing average, monthly profit" },
  { perm: "manage_business", module: "", href: "#/setup", title: "Setup", text: "Locations, items, suppliers, users, roles" },
];

export const routes = [
  { path: "/", auth: "user", render: async (el) => {
    if (state.me?.role === "admin" && !state.me?.tenant) { location.hash = "#/platform"; return; }
    const b = await biz(true);
    const tiles = TILES.filter((t) => has(t.perm) && (!t.module || on(b, t.module)));
    el.innerHTML = `<div class="hero"><h1>${esc(b.business?.name || "")}</h1><p>Hello ${esc(state.me?.name || "")} · ${new Date().toLocaleDateString()}</p></div>
      <div class="grid">${tiles.map((t) => `<a class="card tile" href="${t.href}"><h2>${esc(t.title)}</h2><p class="muted">${esc(t.text)}</p></a>`).join("")
      || '<div class="card"><p>Your account has no tasks yet - ask your owner to give you a role.</p></div>'}</div>`;
  } },
];
