/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// Inventory control's header and tabs (each tab only for those who may use it).
import { html, pageHead, tabs } from "/assets/kit/index.js";
import { area, head } from "../lib/areas.js";
import { has } from "../lib/business.js";

const TABS = [
  { id: "alerts", label: "Alerts", icon: "alert", href: "#/inventory", show: () => true },
  { id: "par", label: "Min / max", icon: "trend", href: "#/inventory/par", show: () => true },
  { id: "takes", label: "Stock take", icon: "clipboard", href: "#/inventory/takes", show: () => has("adjust_stock") || has("manage_business") },
  { id: "value", label: "Valuation", icon: "coin", href: "#/inventory/value", show: () => has("view_costs") || has("manage_business") },
  { id: "analysis", label: "ABC & cover", icon: "chart", href: "#/inventory/analysis", show: () => true },
];

export function frame(el, current, subtitle, actions = "") {
  el.style.setProperty("--area", area("inventory"));
  el.innerHTML = String(html`${pageHead({ ...head("inventory"), title: "Inventory control", subtitle, actions })}${tabs(TABS.filter((t) => t.show()), current)}<div class="k-body"></div>`);
  return el.querySelector(".k-body");
}
