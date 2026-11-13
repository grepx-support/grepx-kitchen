/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// What the order screens share: the page header with its tabs, and receiving an order in a dialog.
import { api, run } from "/assets/app.js";
import { Basket, h, html, openDialog, pageHead, tabs } from "/assets/kit/index.js";
import { head } from "../lib/areas.js";
import { has } from "../lib/business.js";

export function frame(el, current, subtitle = "") {
  const list = [{ id: "board", label: "Board", icon: "board", href: "#/orders" }, { id: "list", label: "List", icon: "list", href: "#/orders/list" }];
  if (has("orders")) list.push({ id: "recommend", label: "Recommended", icon: "sparkle", href: "#/orders/recommended" },
    { id: "new", label: "New order", icon: "plus", href: "#/orders/new" });
  el.innerHTML = String(html`${pageHead({ ...head("orders"), title: "Orders", subtitle })}${tabs(list, current)}<div class="k-body"></div>`);
  el.style.setProperty("--area", head("orders").area);
  return el.querySelector(".k-body");
}

/** Ask for the quantities that arrived and receive them into stock. Resolves true when received. */
export async function receive(order) {
  const slot = h("div");
  const basket = new Basket({ label: "Received", lines: order.lines.map((l) => ({ item_id: l.item_id, name: l.item_name, unit: l.unit, qty: l.qty, hint: `ordered ${l.qty}` })) });
  basket.mount(slot);
  slot.prepend(h("p", { class: "muted" }, "Change a quantity if the delivery differs, then receive it into stock."));
  const go = await openDialog({ title: `Receive ${order.number}`, body: slot, actions: [{ label: "Back", value: "" }, { label: "Receive into stock", value: "yes", primary: true }] });
  if (go !== "yes") return false;
  return !!(await run(() => api(`/orders/${order.id}/receive`, { method: "POST", body: { lines: basket.lines(true) } }), `${order.number} received`));
}
