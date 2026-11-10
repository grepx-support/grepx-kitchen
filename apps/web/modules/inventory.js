/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// Inventory control: alerts, minimum / maximum levels, stock takes, valuation, ABC and days of cover.
import { alerts } from "./inventory/alerts.js";
import { par } from "./inventory/par.js";
import { analysis, value } from "./inventory/reports.js";
import { take, takes } from "./inventory/takes.js";

const INV = { auth: "staff", tenant: true, area: "inventory", group: "Warehouse" };

export const routes = [
  { path: "/inventory", nav: "Inventory control", icon: "alert", perm: "view_stock", ...INV, render: alerts },
  { path: "/inventory/par", perm: "view_stock", ...INV, render: par },
  { path: "/inventory/takes", perm: "adjust_stock", ...INV, render: takes },
  { path: "/inventory/take/:id", perm: "adjust_stock", ...INV, render: (el, { args }) => take(el, args[0]) },
  { path: "/inventory/value", perm: "view_costs", ...INV, render: value },
  { path: "/inventory/analysis", perm: "view_stock", ...INV, render: analysis },
];
