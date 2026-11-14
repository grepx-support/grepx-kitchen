/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// Dispatch board: trips waiting for a run on the left, each open run as a column - drag a trip onto a run (or back).
import { api, run, toast } from "/assets/app.js";
import { h, html, icon, KanbanBoard, pageHead, pill } from "/assets/kit/index.js";
import { area, head } from "../lib/areas.js";
import { today } from "../lib/format.js";
import { showTrip } from "../lib/trip.js";

const RUN_COLORS = ["#7c3aed", "#0891b2", "#f97316", "#16a34a", "#e11d48", "#2563eb"];

export async function board(el) {
  const d = await api("/runs");
  el.style.setProperty("--area", area("runs"));
  el.innerHTML = String(html`${pageHead({ ...head("runs"), title: "Delivery runs", subtitle: "Plan each driver's day: drag trips onto a run, open a run to set the order and start it." })}
    <form class="card accent k-bar" data-plan><label>Date<input type="date" name="date" value="${today()}"></label>
      <label>Driver<select name="driver_id"><option value="">-</option>${d.drivers.map((x) => html`<option value="${x.id}">${x.name}</option>`)}</select></label>
      <label>Leaves at<input type="time" name="start_time" value="08:00"></label><label>Vehicle<input name="vehicle" placeholder="Van 1"></label>
      <button class="btn primary">${icon("plus", { size: 16 })} New run with the ticked trips</button></form><div class="slot k-section"></div>`);
  const columns = [{ id: "waiting", title: "Waiting for a run", icon: "inbox", color: "#64748b", hint: "Sent from the warehouse, not on a run yet" },
    ...d.runs.filter((r) => r.state === "planned" || r.state === "on_road").map((r, n) => ({ id: r.id, title: `${r.name}`, icon: "truck",
      color: RUN_COLORS[n % RUN_COLORS.length], hint: `${r.driver_name || "no driver"} · ${r.date} ${r.start_time} · ${r.state === "on_road" ? "on the road" : "planned"}` }))];
  const cards = [...d.waiting.map((t) => ({ ...t, column: "waiting" })),
    ...d.runs.flatMap((r) => (r.stops || []).filter((s) => s.state === "pending" || s.state === "arrived").map((s) => ({ id: s.stop_id, to: s.name, address: s.address,
      lines: s.lines, eta: s.eta, column: r.id, state: s.state, delivery_id: s.delivery_id })))];
  const slot = el.querySelector(".slot");
  new KanbanBoard({ columns, cards, empty: "Drop trips here",
    card: (c) => html`${c.column === "waiting" ? html`<label class="check"><input type="checkbox" data-tick="${c.id}"> <b>→ ${c.to}</b></label>` : html`<b>→ ${c.to}</b>`}
      <p class="muted small">${c.address || "no address"}</p><p>${pill(`${c.lines} lines`, "info")} ${c.eta ? pill(`ETA ${c.eta}`, "warn") : ""} ${c.date ? html`<span class="muted small">${c.date}</span>` : ""}</p>`,
    onOpen: (c) => showTrip(c.delivery_id || c.id),
    onMove: (c, from, to) => move(d, c, from, to) }).mount(slot);
  slot.append(h("p", { class: "muted small" }, "Open a run to put its stops in order:"));
  d.runs.forEach((r) => slot.append(h("a", { class: "btn small", href: `#/runs/${r.id}` }, `${r.name} - ${r.stops.length} stop${r.stops.length === 1 ? "" : "s"}`)));
  el.querySelector("[data-plan]").onsubmit = async (e) => {
    e.preventDefault();
    const ids = [...el.querySelectorAll("[data-tick]:checked")].map((x) => x.dataset.tick);
    if (!ids.length) return toast("Tick the trips for this run.");
    const f = new FormData(e.target);
    const r = await run(() => api("/runs", { method: "POST", body: { date: f.get("date"), driver_id: f.get("driver_id"), start_time: f.get("start_time"),
      vehicle: f.get("vehicle"), delivery_ids: ids } }), "Run planned");
    if (r) location.hash = `#/runs/${r.run_id}`;
  };
}

async function move(d, card, from, to) {
  const stopsOf = (id) => (d.runs.find((r) => r.id === id)?.stops || []).filter((s) => s.state === "pending" || s.state === "arrived").map((s) => s.stop_id);
  const steps = [];
  if (from !== "waiting") steps.push([from, stopsOf(from).filter((s) => s !== card.id)]);
  if (to !== "waiting") steps.push([to, [...stopsOf(to), card.id]]);
  for (const [runId, ids] of steps) {
    if (!ids.length) { toast("A run needs at least one stop - cancel the run instead."); return false; }
    if (!(await run(() => api(`/runs/${runId}/stops`, { method: "POST", body: { delivery_ids: ids } })))) return false;
  }
  setTimeout(() => window.dispatchEvent(new HashChangeEvent("hashchange")), 50);     // redraw with the new estimates
  return true;
}
