/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// The kitchen screen: target cards, ingredients against need, and recording what was made and used (drag in or tap +).
import { api, run, state, toast } from "/assets/app.js";
import { Builder, html, icon, pageHead } from "/assets/kit/index.js";
import { area, head } from "../lib/areas.js";
import { biz, has } from "../lib/business.js";
import { fmt, time } from "../lib/format.js";
import { catalogue, finished, notFinished } from "../lib/items.js";
import { isKitchen, picker, remember, remembered } from "../lib/place.js";
import { history, ingredients, targetCards } from "./target.js";
import { manualTarget, wireManualTarget } from "./manual-target.js";

export async function kitchen(el, q) {
  const b = await biz();
  const loc = q.location || remembered(b.locations, isKitchen);
  el.style.setProperty("--area", area("kitchen"));
  if (!loc) { el.innerHTML = '<div class="card"><p>No kitchen set up yet.</p></div>'; return; }
  remember(loc);
  const [t, day, items] = await Promise.all([api(`/kitchen/target?location_id=${loc}`), api(`/kitchen/today?location_id=${loc}`), catalogue()]);
  el.innerHTML = String(html`${pageHead({ ...head("kitchen"), title: "Kitchen", subtitle: `Week of ${t.week} · ${state.me?.name || ""}`, actions: picker(b.locations, loc, isKitchen, "location", "Kitchen") })}
    ${history(t)}${targetCards(t)}
    ${t.ingredients.length ? html`<section class="card accent k-section"><h2>${icon("box")} Ingredients for the target</h2>${ingredients(t)}</section>` : ""}
    ${has("manage_business") ? manualTarget(t) : ""}
    <div class="stack k-section"><section class="card accent"><h2>${icon("pot")} Record production</h2><div class="prod"></div>
        <p><button class="btn primary" data-prod>Save production run</button></p></section>
      <section class="card accent"><h2>${icon("box")} Record ingredients used</h2><div class="use"></div>
        <p><button class="btn primary" data-use>Save ingredients used</button></p></section></div>
    <section class="card k-section"><h2>${icon("clock")} Recorded today</h2><ul class="k-feed">${day.records.map((r) => html`<li style="--c:${r.kind === "produce" ? area("kitchen") : "#94a3b8"}"><i></i>
      <span class="k-feed-what"><span><b>${r.kind === "produce" ? "Made" : "Used"}</b> · ${r.item_name}</span><small>${r.by}</small></span><b>${fmt(r.qty)} ${r.unit}</b><time>${time(r.at)}</time></li>`)}</ul>
      ${day.records.length ? "" : html`<p class="muted">Nothing yet.</p>`}</section>`);
  const prod = new Builder({ items: items.filter(finished), title: "Products", label: "Made",
    lines: t.lines.map((l) => ({ item_id: l.item_id, name: l.name, unit: l.unit, qty: "", hint: l.target ? `target ${fmt(l.target)}` : "" })) });
  const use = new Builder({ items: items.filter(notFinished), title: "Ingredients", label: "Used",
    lines: t.ingredients.map((i) => ({ item_id: i.item_id, name: i.name, unit: i.unit, qty: "", hint: `target needs ${fmt(i.needed)}` })) });
  prod.mount(el.querySelector(".prod"));
  use.mount(el.querySelector(".use"));
  const again = () => kitchen(el, { location: loc });
  el.querySelector("[data-pick]").onchange = (e) => { remember(e.target.value); kitchen(el, { location: e.target.value }); };
  el.querySelector("[data-prod]").onclick = () => save(prod, "/kitchen/production", loc, "Enter what you made.", "Production saved", again);
  el.querySelector("[data-use]").onclick = () => save(use, "/kitchen/use", loc, "Enter what you used.", "Ingredients saved", again);
  wireManualTarget(el, again);
}

async function save(builder, path, loc, nothing, done, again) {
  const lines = builder.lines();
  if (!lines.length) return toast(nothing);
  if (await run(() => api(path, { method: "POST", body: { location_id: loc, lines } }), done)) again();
}
