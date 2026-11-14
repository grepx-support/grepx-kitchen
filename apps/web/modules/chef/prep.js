/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// Today's prep list by station: what each station makes today (the week's target spread over the days left, in whole
// batches), minutes of work, made so far; a column per station so the whole kitchen fits on one screen.
import { api } from "/assets/app.js";
import { empty, html, icon } from "/assets/kit/index.js";
import { biz } from "../lib/business.js";
import { isKitchen, picker, remember, remembered } from "../lib/place.js";
import { frame, mins } from "./common.js";

const task = (t) => html`<li class="ch-task ${t.made_today >= t.qty ? "done" : ""}"><a href="#/chef/recipe?id=${t.item_id}&make=${t.qty}"><b>${t.name}</b></a>
  <span class="ch-q">${t.qty} ${t.unit}${t.batches ? ` · ${t.batches} batch${t.batches > 1 ? "es" : ""}` : ""}</span>
  <span class="muted small">${mins(t.minutes) || "no times on the card"}${t.made_today ? ` · made ${t.made_today} today` : ""}${t.has_card ? "" : " · no method yet"}</span></li>`;

export async function prepPage(el, q) {
  const b = await biz();
  const loc = q.location || remembered(b.locations, isKitchen);
  if (!loc) { el.innerHTML = '<div class="card"><p>No kitchen set up yet.</p></div>'; return; }
  remember(loc);
  const p = await api(`/chef/prep?location_id=${loc}`);
  const body = await frame(el, "prep", "Prep list", `${p.date} · ${p.days_left} day${p.days_left > 1 ? "s" : ""} left this week`,
    html`${picker(b.locations, loc, isKitchen, "location", "Kitchen")} <button class="btn" onclick="print()">${icon("printer", { size: 16 })} Print</button>`);
  el.querySelector("[data-pick]").onchange = (e) => { remember(e.target.value); prepPage(el, { location: e.target.value }); };
  body.innerHTML = String(p.stations.length ? html`<div class="ch-board">${p.stations.map((s) => html`<section class="card ch-col">
      <header><b>${s.station}</b><span class="muted small">${s.tasks.length} · ${mins(s.minutes) || "-"}</span></header><ul>${s.tasks.map(task)}</ul></section>`)}</div>`
    : empty({ icon: "check", title: "Nothing to prep", text: "This week's target is met - or no targets yet (Kitchen screen)." }));
}
