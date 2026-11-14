/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// The delivery board: every warehouse-out trip is "On the way" until it is dragged to "Delivered" at the destination.
import { api, run } from "/assets/app.js";
import { html, KanbanBoard } from "/assets/kit/index.js";
import { fmt, time, today } from "../lib/format.js";
import { openPdf } from "../money/common.js";
import { frame } from "./common.js";

export async function deliveries(el, q) {
  const day = q.date ?? today();
  const d = await api(`/stock/deliveries${day ? `?date=${day}` : ""}`);
  const body = frame(el, "deliveries", { title: "Deliveries", subtitle: "Drag a trip to Delivered when it arrives - stock already moved when it was sent.",
    actions: html`<div class="kit-chips"><a class="kit-chip ${day ? "on" : ""}" href="#/stock/deliveries">Today</a><a class="kit-chip ${day ? "" : "on"}" href="#/stock/deliveries?date=">All days</a></div>` });
  new KanbanBoard({
    empty: "No trips",
    cards: d.deliveries.map((t) => ({ ...t, column: t.state })),
    columns: [{ id: "sent", title: "On the way", icon: "truck", color: "#f59e0b", accepts: () => false },
      { id: "delivered", title: "Delivered", icon: "check", color: "#16a34a", accepts: (c, from) => from === "sent" }],
    card: (t) => html`<p><b>${t.from} → ${t.to}</b></p><p class="muted small">${t.date} ${time(t.at)} · sent by ${t.by}</p>
      ${t.lines.map((l) => html`<div class="k-row"><span>${l.item_name}</span><b>${fmt(l.qty)} ${l.unit}</b></div>`)}
      ${t.state === "delivered" && t.delivered_by ? html`<p class="ok small">✓ ${t.delivered_by} ${time(t.delivered_at)}</p>` : ""}
      <p><a href="javascript:void 0" class="small" data-note="${t.id}">Delivery note (PDF)</a></p>`,
    onMove: async (t) => !!(await run(() => api(`/stock/deliveries/${t.id}/delivered`, { method: "POST", body: {} }), `Delivered to ${t.to}`)),
  }).mount(body);
  body.addEventListener("click", (e) => { const a = e.target.closest("[data-note]"); if (a) { e.stopPropagation(); openPdf(`/pdf/delivery/${a.dataset.note}`); } });
}
