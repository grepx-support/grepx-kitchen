/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// Alerts: expired, below zero, expiring, below minimum - each with what to do next. Checked every hour; owners get a message.
import { api, run } from "/assets/app.js";
import { empty, html, icon, kpiRow } from "/assets/kit/index.js";
import { fmt } from "../lib/format.js";
import { frame } from "./common.js";

const KIND = {
  expired: ["Expired", "#e11d48", "alert", (a) => html`<a class="btn small" href="#/warehouse?location=${a.location_id}">Throw away</a>`],
  negative: ["Below zero", "#be123c", "alert", () => html`<a class="btn small" href="#/inventory/takes">Count it</a>`],
  expiring: ["Expiring", "#f59e0b", "clock", (a) => html`<a class="btn small" href="#/warehouse?location=${a.location_id}">Use first</a>`],
  low: ["Below minimum", "#0ea5e9", "trend", () => html`<a class="btn small" href="#/orders/recommended">Order</a>`],
};

export async function alerts(el) {
  const { alerts: list } = await api("/inventory/alerts");
  const body = frame(el, "alerts", "Checked every hour - the owners get one message a day with the new ones.",
    html`<button class="btn small primary" data-check>${icon("refresh", { size: 15 })} Check now</button>`);
  const n = (k) => list.filter((a) => a.kind === k).length;
  body.innerHTML = String(html`${kpiRow(Object.entries(KIND).map(([k, [label, color, ic]]) => ({ label, value: n(k), icon: ic, area: color, tone: n(k) ? "bad" : "good" })))}
    ${list.length ? html`<div class="stack">${list.map((a) => { const [label, color, ic, act] = KIND[a.kind];
      return html`<article class="card k-alert" style="--area:${color}"><span class="kit-wicon">${icon(ic)}</span>
        <div><b>${a.item_name}</b> at ${a.location_name}<p class="muted small">${label} · ${fmt(a.qty)} ${a.unit}${a.limit ? ` (minimum ${fmt(a.limit)}, fill to ${fmt(a.fill_to)})` : ""}${a.expiry ? ` · expiry ${a.expiry}` : ""} · ${a.date}</p></div>
        <span class="row">${act(a)}<button class="btn small" data-done="${a.id}">Done</button></span></article>`; })}</div>`
      : empty({ icon: "check", title: "No open alerts", text: "Stock is above its minimums and nothing is about to expire." })}`);
  body.querySelectorAll("[data-done]").forEach((b) => b.onclick = async () => { if (await run(() => api(`/inventory/alerts/${encodeURIComponent(b.dataset.done)}/done`, { method: "POST" }))) alerts(el); });
  el.querySelector("[data-check]").onclick = async () => {
    const r = await run(() => api("/inventory/alerts/check", { method: "POST" }));
    if (r) { alerts(el); }
  };
}
