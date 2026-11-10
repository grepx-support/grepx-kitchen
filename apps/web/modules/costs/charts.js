/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// The cost charts: COGS / costing by count period (with the target band), sales by period, where the money went.
import { columnChart, donut, html, lineChart } from "/assets/kit/index.js";
import { area } from "../lib/areas.js";
import { fmt } from "../lib/format.js";

export const trend = (days, s) => lineChart({ labels: days.map((x) => x.date.slice(5)), unit: "%", band: s.cogs_range, label: "COGS and costing by day",
  series: [{ name: "COGS %", color: area("costs"), values: days.map((x) => x.cogs_pct) }, { name: "Costing %", color: "#f59e0b", values: days.map((x) => x.costing_pct) }] });

export const sales = (days) => columnChart({ labels: days.map((x) => x.date.slice(5)), values: days.map((x) => x.sales || 0), color: "#0ea5e9", label: "Sales by day" });

export const split = (s, b) => donut({ centre: fmt(s.sales, 0), caption: `sales ${b.business?.currency || ""}`, label: "Where the money went", parts: [
  { label: "Ingredients", value: s.ingredient_cost, color: "#f97316" }, { label: "Labour", value: s.labour, color: "#8b5cf6" },
  { label: "Rent", value: s.rent, color: "#0ea5e9" }, { label: "Other", value: s.other, color: "#94a3b8" },
  { label: "Profit", value: Math.max(0, s.net_profit || 0), color: "#16a34a" }] });

export const missing = (s) => (s.missing.length ? html`<p class="kit-pill bad">Missing: ${s.missing.join(", ")} - profit shows when every cost is in.</p>` : "");
