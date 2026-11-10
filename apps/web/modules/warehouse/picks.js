/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// Pick lists: start one for a destination (the warehouse-out suggestion is already in it, drag in more), then pick it.
import { api, run, toast } from "/assets/app.js";
import { Builder, html, icon, pill } from "/assets/kit/index.js";
import { fmt, stamp } from "../lib/format.js";
import { catalogue } from "../lib/items.js";
import { notHolding, picker, remembered } from "../lib/place.js";
import { frame } from "./common.js";

export async function picks(el, q, b, place) {
  const f = await api(`/warehouse?location_id=${place}`);
  const to = q.to || remembered(b.locations, notHolding);
  const [plan, items] = await Promise.all([to ? api(`/stock/warehouse-out?to_location_id=${to}`).catch(() => ({ lines: [] })) : { lines: [] }, catalogue()]);
  const body = frame(el, "picks", b, f.location_id, "A pick list tells the picker which bin and which lot to take; done = sent.");
  body.innerHTML = String(html`${f.picks.length ? html`<section class="card accent"><h2>${icon("list")} Open pick lists</h2>${f.picks.map((p) => html`
      <a class="k-row" href="#/warehouse/pick/${p.id}"><b>→ ${f.places[p.to_location_id] || ""}</b><span>${p.lines.length} lines · ${stamp(p.created_at)} · ${p.by_name}</span>
        ${pill(`${p.lines.filter((l) => l.picked > 0).length}/${p.lines.length} picked`, "info")}</a>`)}</section>` : ""}
    <section class="card accent k-section"><div class="k-bar">${picker(b.locations, to, notHolding, "to", "Pick for")}
      <button class="btn primary" data-create>${icon("list", { size: 16 })} Create pick list</button></div><div class="slot"></div></section>`);
  const builder = new Builder({ items, title: "Items", label: "Pick", scan: true,
    lines: plan.lines.filter((l) => l.suggested).map((l) => ({ item_id: l.item_id, name: l.name, unit: l.unit, qty: l.suggested, hint: `there ${fmt(l.at_location)}` })) });
  builder.mount(body.querySelector(".slot"));
  body.querySelector('[name="to"]').onchange = (e) => picks(el, { ...q, to: e.target.value }, b, place);
  body.querySelector("[data-create]").onclick = async () => {
    const lines = builder.lines();
    if (!lines.length) return toast("Add what to pick.");
    const p = await run(() => api("/warehouse/picks", { method: "POST", body: { from_location_id: f.location_id, to_location_id: body.querySelector('[name="to"]').value, lines } }), "Pick list ready");
    if (p) location.hash = `#/warehouse/pick/${p.pick_id}`;
  };
}
