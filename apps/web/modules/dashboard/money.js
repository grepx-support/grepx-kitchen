/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// Where this month's sales went: ingredients, labour, rent, other, and what is left - the donut, then each part as a
// share of sales against a typical restaurant range (food 25-35%, labour 25-35%, rent 6-10%), and the net margin.
import { api } from "/assets/app.js";
import { donut, html } from "/assets/kit/index.js";
import { area } from "../lib/areas.js";
import { has, on } from "../lib/business.js";
import { fmt, money, pct, thisMonth } from "../lib/format.js";

// share of sales a healthy restaurant usually stays within (green inside, amber above)
const PARTS = [["Ingredients", "ingredient_cost", "#f97316", 35, "#/inventory/value"], ["Labour", "labour", "#8b5cf6", 35, "#/payroll"],
  ["Rent", "rent", "#0ea5e9", 10, "#/costs"], ["Other", "other", "#94a3b8", 10, "#/costs"]];

const shares = (s, b) => html`<div class="k-shares">${PARTS.map(([label, key, color, high, href]) => {
  const share = s.sales ? (s[key] || 0) / s.sales * 100 : 0;
  return html`<a class="k-share" href="${href}"><span>${label}</span><i><b style="width:${Math.min(100, share)}%;background:${color}"></b><em style="left:${high}%"></em></i>
    <span class="${share > high ? "bad" : "ok"}">${pct(share)}</span></a>`;
})}<p class="k-net ${s.net_profit === null ? "muted" : s.net_profit < 0 ? "bad" : "ok"}">Net profit: <b>${s.net_profit === null ? "not yet" : money(b, s.net_profit)}</b>
  ${s.sales && s.net_profit !== null ? html`<span class="muted"> · ${pct(s.net_profit / s.sales * 100)} of sales</span>` : ""}</p></div>`;

export default {
  id: "money", title: "Month so far", icon: "coin", area: area("costs"), href: "#/costs",
  allowed: ({ b }) => has("view_costs") && on(b, "costing"),
  load: () => api(`/costs/month?month=${thisMonth()}`),
  render: (s, { b }) => html`${donut({ centre: fmt(s.sales, 0), caption: `sales ${b.business?.currency || ""}`, label: "Month split", parts: [
      { label: "Ingredients", value: s.ingredient_cost, color: "#f97316", href: "#/inventory/value" }, { label: "Labour", value: s.labour, color: "#8b5cf6", href: "#/payroll" },
      { label: "Rent", value: s.rent, color: "#0ea5e9", href: "#/costs" }, { label: "Other", value: s.other, color: "#94a3b8", href: "#/costs" },
      { label: "Profit", value: Math.max(0, s.net_profit || 0), color: "#16a34a", href: "#/money/margins" }] })}
    ${shares(s, b)}`,
};
