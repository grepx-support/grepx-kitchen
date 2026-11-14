/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// The stock screens share one header with tabs; each tab shows only to those allowed to use it.
import { html, pageHead, tabs } from "/assets/kit/index.js";
import { area, head } from "../lib/areas.js";
import { has } from "../lib/business.js";

const TABS = [
  { id: "levels", label: "Levels", icon: "box", href: "#/stock", perm: "view_stock", area: "stock" },
  { id: "out", label: "Warehouse out", icon: "outbox", href: "#/stock/out", perm: "warehouse_out", area: "out" },
  { id: "in", label: "Warehouse in", icon: "inbox", href: "#/stock/in", perm: "warehouse_in", area: "in" },
  { id: "move", label: "Transfer & adjust", icon: "swap", href: "#/stock/move", perm: "transfer", area: "move" },
  { id: "deliveries", label: "Deliveries", icon: "truck", href: "#/stock/deliveries", perm: "delivery", also: "warehouse_out", area: "deliveries" },
];

export function frame(el, current, { title, subtitle = "", actions = "" }) {
  const tab = TABS.find((t) => t.id === current);
  const mine = TABS.filter((t) => has(t.perm) || (t.also && has(t.also)));
  el.style.setProperty("--area", area(tab.area));
  el.innerHTML = String(html`${pageHead({ ...head(tab.area), title, subtitle, actions })}${mine.length > 1 ? tabs(mine, current) : ""}<div class="k-body"></div>`);
  return el.querySelector(".k-body");
}
