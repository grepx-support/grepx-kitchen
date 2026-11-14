/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// One run: stops in order with arrival estimates (drag to reorder while planned), a map route link, start / cancel.
import { api, run } from "/assets/app.js";
import { confirm, html, icon, pageHead, pill, progress, SortableList } from "/assets/kit/index.js";
import { area, head } from "../lib/areas.js";
import { time } from "../lib/format.js";
import { openPdf } from "../money/common.js";

const TONE = { pending: "", arrived: "info", delivered: "good", failed: "bad" };

export const routeLink = (stops) => {
  const open = stops.filter((s) => s.address && (s.state === "pending" || s.state === "arrived"));
  return open.length ? `https://www.google.com/maps/dir/${open.map((s) => encodeURIComponent(s.address)).join("/")}` : "";
};

export async function runPage(el, id) {
  const d = await api("/runs?date=");
  const r = [...d.runs].find((x) => x.id === id) || (await api("/runs/mine")).runs.find((x) => x.id === id);
  el.style.setProperty("--area", area("runs"));
  if (!r) { el.innerHTML = '<div class="card"><p>This run is finished or was cancelled.</p><p><a class="btn" href="#/runs">Back to runs</a></p></div>'; return; }
  const closed = r.stops.filter((s) => s.state === "delivered" || s.state === "failed").length;
  const map = routeLink(r.stops);
  el.innerHTML = String(html`${pageHead({ ...head("runs"), title: r.name, subtitle: `${r.driver_name || "no driver"} · ${r.vehicle || "vehicle not set"} · ${r.date} from ${r.start_time}`,
      actions: html`${pill(r.state.replace("_", " "), r.state === "on_road" ? "warn" : "info")}${map ? html`<a class="btn small" target="_blank" rel="noopener" href="${map}">${icon("map", { size: 15 })} Route</a>` : ""}` })}
    ${progress(closed, r.stops.length, { label: "Stops done" })}
    <section class="card k-section"><h2>${icon("pin")} Stops ${r.state === "planned" ? html`<small class="muted">drag to change the order</small>` : ""}</h2>
      <ol class="k-sort k-stops">${r.stops.map((s, n) => html`<li data-id="${s.stop_id}" class="${s.state}">
        ${r.state === "planned" && s.state === "pending" ? html`<button type="button" class="kit-grip" aria-label="Move ${s.name}">${icon("grip", { size: 16 })}</button>` : html`<span></span>`}
        <span class="tag">${n + 1}</span><span class="who"><b>${s.name}</b><small>${s.address || "no address"} · ${s.lines} lines</small>
          ${s.receiver ? html`<small class="ok">✓ ${s.receiver} at ${time(s.delivered_at)}</small>` : ""}
          <a href="javascript:void 0" class="small" data-note="${s.delivery_id}">${icon("printer", { size: 13 })} Delivery note</a>${s.fail_reason ? html`<small class="bad">✗ ${s.fail_reason}</small>` : ""}</span>
        <span>${s.eta ? pill(`ETA ${s.eta}`, "warn") : pill(s.state, TONE[s.state])}</span></li>`)}</ol></section>
    <div class="k-nav"><a class="btn" href="#/runs">${icon("board", { size: 15 })} All runs</a><span>
      ${r.state === "planned" ? html`<button class="btn" data-cancel>Cancel run</button> <button class="btn primary" data-start>${icon("truck", { size: 16 })} Start run</button>` : ""}
      ${r.state === "on_road" ? html`<a class="btn primary" href="#/driver">${icon("truck", { size: 16 })} Driver view</a>` : ""}</span></div>`);
  const again = () => runPage(el, id);
  el.querySelectorAll("[data-note]").forEach((a) => a.addEventListener("click", () => openPdf(`/pdf/delivery/${a.dataset.note}`)));
  if (r.state === "planned") {
    new SortableList(el.querySelector(".k-stops"), { onChange: async (ids) => {
      if (await run(() => api(`/runs/${id}/stops`, { method: "POST", body: { delivery_ids: ids } }), "Order saved")) again();
    } });
  }
  el.querySelector("[data-start]")?.addEventListener("click", async () => { if (await run(() => api(`/runs/${id}/start`, { method: "POST" }), "On the road")) again(); });
  el.querySelector("[data-cancel]")?.addEventListener("click", async () => {
    if (await confirm({ title: "Cancel this run?", text: "Its trips go back to waiting.", ok: "Cancel run", danger: true })
      && await run(() => api(`/runs/${id}/cancel`, { method: "POST" }))) location.hash = "#/runs";
  });
}
