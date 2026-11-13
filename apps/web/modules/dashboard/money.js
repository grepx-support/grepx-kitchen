/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// Where this month's sales went: ingredients, labour, rent, other, and what is left.
import { api } from "/assets/app.js";
import { donut, html } from "/assets/kit/index.js";
import { area } from "../lib/areas.js";
import { has, on } from "../lib/business.js";
import { fmt, money, thisMonth } from "../lib/format.js";

export default {
  id: "money", title: "Month so far", icon: "coin", area: area("costs"), href: "#/costs",
  allowed: ({ b }) => has("view_costs") && on(b, "costing"),
  load: () => api(`/costs/month?month=${thisMonth()}`),
  render: (s, { b }) => html`${donut({ centre: fmt(s.sales, 0), caption: `sales ${b.business?.currency || ""}`, label: "Month split", parts: [
      { label: "Ingredients", value: s.ingredient_cost, color: "#f97316", href: "#/inventory/value" }, { label: "Labour", value: s.labour, color: "#8b5cf6", href: "#/costs" },
      { label: "Rent", value: s.rent, color: "#0ea5e9", href: "#/costs" }, { label: "Other", value: s.other, color: "#94a3b8", href: "#/costs" },
      { label: "Profit", value: Math.max(0, s.net_profit || 0), color: "#16a34a", href: "#/money/margins" }] })}
    <p class="k-net ${s.net_profit === null ? "muted" : s.net_profit < 0 ? "bad" : "ok"}">Net profit: <b>${s.net_profit === null ? "not yet" : money(b, s.net_profit)}</b></p>`,
};
