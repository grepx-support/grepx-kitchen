/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// Purchase orders as a board: drag an order from "On order" to "Received" (enter what arrived) or "Cancelled".
import { api, run } from "/assets/app.js";
import { confirm, html, KanbanBoard, pill } from "/assets/kit/index.js";
import { biz, has } from "../lib/business.js";
import { money, stamp } from "../lib/format.js";
import { frame, receive } from "./common.js";

const fromSaved = (card, from) => from === "saved";

export async function board(el) {
  const body = frame(el, "board", "Drag an order to Received when it arrives, or open it to change, copy or send it.");
  const [b, d] = await Promise.all([biz(), api("/orders")]);
  const cards = d.orders.map((o) => ({ ...o, column: o.state === "received" ? "received" : o.state === "cancelled" ? "cancelled" : "saved" }));
  new KanbanBoard({
    cards,
    empty: "No orders here",
    columns: [
      { id: "saved", title: "On order", icon: "clock", color: "#7c3aed", accepts: () => false, hint: "Saved and sent to the supplier" },
      { id: "received", title: "Received", icon: "check", color: "#16a34a", accepts: fromSaved, hint: "In stock" },
      ...(has("orders") ? [{ id: "cancelled", title: "Cancelled", icon: "x", color: "#94a3b8", accepts: fromSaved }] : []),
    ],
    card: (o) => html`<a href="#/orders/${o.id}" class="k-card-link"><b>${o.number}</b></a> ${pill(`${o.lines.length} line${o.lines.length === 1 ? "" : "s"}`, "info")}
      <p>${o.supplier_name || ""}</p><p class="muted small">${stamp(o.created_at)} · ${o.created_by_name || ""}</p>
      ${o.value !== undefined ? html`<p><b>${money(b, o.value)}</b></p>` : ""}`,
    onMove: async (o, from, to) => {
      if (to === "received") return receive(o);
      if (!(await confirm({ title: `Cancel ${o.number}?`, text: "The supplier order is cancelled; nothing is received.", ok: "Cancel order", cancel: "Keep it", danger: true }))) return false;
      return !!(await run(() => api(`/orders/${o.id}/cancel`, { method: "POST" }), `${o.number} cancelled`));
    },
  }).mount(body);
}
