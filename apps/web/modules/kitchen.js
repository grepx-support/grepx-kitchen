/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// Kitchen: the target on the phone (KIT-03..05), record a production run and the ingredients used (KIT-06..09).
import { api, esc, run, state, toast } from "../../app.js";
import { biz, fmt, has, lines, picker, readLines, remember, remembered, wireLines } from "./lib.js";

const kitchens = (l) => l.kind === "kitchen";

export const routes = [
  { path: "/kitchen", nav: "Kitchen", auth: "staff", perm: "kitchen", render: async function draw(el, q) {
    const b = await biz();
    const loc = q.location || remembered(b.locations, kitchens);
    if (!loc) { el.innerHTML = '<div class="card"><p>No kitchen set up yet.</p></div>'; return; }
    remember(loc);
    const [t, today, stock] = await Promise.all([api(`/kitchen/target?location_id=${loc}`), api(`/kitchen/today?location_id=${loc}`),
      api(`/stock?location_id=${loc}`).catch(() => ({ levels: [] }))]);
    const items = {}; (stock.levels || []).forEach((s) => { items[s.item_id] = { id: s.item_id, name: s.item_name, unit: s.unit }; });
    const finished = {}; t.lines.forEach((l) => { finished[l.item_id] = { id: l.item_id, name: l.name, unit: l.unit }; });
    t.ingredients.forEach((i) => { items[i.item_id] = items[i.item_id] || { id: i.item_id, name: i.name, unit: i.unit }; });
    el.innerHTML = `<h1>Kitchen</h1><div class="row"><div><label>Kitchen</label>${picker(b.locations, loc, kitchens)}</div></div>
      <div class="card"><h2>This week's target <span class="muted small">week of ${esc(t.week)}</span></h2>
        ${t.has_history ? `<p class="muted">From the last ${esc(t.history_days)} days of usage, plus safety buffer, minus stock on hand.</p>` :
          '<p class="bad">No usage history yet - the owner types this week\'s target by hand.</p>'}
        <table><tr><th>Make</th><th>Target</th><th>Batches</th><th>On hand</th></tr>
        ${t.lines.map((l) => `<tr><td>${esc(l.name)}${l.source === "manual" ? ' <span class="badge">set by hand</span>' : ""}${l.extra ? ` <span class="badge">+${fmt(l.extra)} event</span>` : ""}</td>
          <td><b>${l.target === null ? "–" : fmt(l.target)}</b> ${esc(l.unit)}</td><td>${l.batches ?? "–"}${l.batch_output ? ` <span class="muted small">× ${fmt(l.batch_output)}</span>` : ""}</td>
          <td>${fmt(l.on_hand)}</td></tr>`).join("")}</table>
        ${t.ingredients.length ? `<h2 style="margin-top:14px">Ingredients for the target</h2><table><tr><th>Ingredient</th><th>Needed</th><th>On hand</th><th>To buy</th></tr>
          ${t.ingredients.map((i) => `<tr><td>${esc(i.name)}</td><td>${fmt(i.needed)} ${esc(i.unit)}</td><td>${fmt(i.on_hand)}</td><td class="${i.to_buy ? "bad" : "ok"}">${fmt(i.to_buy)}</td></tr>`).join("")}</table>` : ""}
        ${has("manage_business") ? `<details><summary>Set a target by hand / event week extra</summary><form id="tgt" class="row">
          <div><label>Product</label><select name="item">${t.lines.map((l) => `<option value="${esc(l.item_id)}">${esc(l.name)}</option>`).join("")}</select></div>
          <div><label>Target (empty = calculated)</label><input name="qty" type="number" inputmode="decimal" min="0" step="any"></div>
          <div><label>Event extra</label><input name="extra" type="number" inputmode="decimal" min="0" step="any"></div><button class="btn">Save</button></form></details>` : ""}
      </div><br>
      <div class="grid"><form class="card" id="prod"><h2>Record production</h2><label>Your name</label><input value="${esc(state.me?.name || "")}" disabled>
          ${lines(t.lines.map((l) => ({ item_id: l.item_id, item_name: l.name, unit: l.unit })), finished, { label: "Made", allowAdd: false })}
          <p><button class="btn primary">Save production run</button></p></form>
        <form class="card" id="use"><h2>Record ingredients used</h2>
          ${lines(t.ingredients.map((i) => ({ item_id: i.item_id, item_name: i.name, unit: i.unit, hint: `target needs ${fmt(i.needed)}` })), items, { label: "Used" })}
          <p><button class="btn primary">Save ingredients used</button></p></form></div><br>
      <div class="card"><h2>Recorded today</h2>${today.records.map((r) => `<div class="item">${r.kind === "produce" ? "Made" : "Used"} <b>${fmt(r.qty)} ${esc(r.unit)}</b> ${esc(r.item_name)} <span class="muted">· ${esc(r.by)} · ${esc((r.at || "").slice(11, 16))}</span></div>`).join("") || '<p class="muted">Nothing yet.</p>'}</div>`;
    el.querySelector("[data-pick]").onchange = (e) => { remember(e.target.value); draw(el, { location: e.target.value }); };
    ["prod", "use"].forEach((id) => wireLines(el.querySelector(`#${id}`), id === "prod" ? finished : items));
    el.querySelector("#prod").onsubmit = async (e) => { e.preventDefault(); const ls = readLines(e.target); if (!ls.length) return toast("Enter what you made.");
      if (await run(() => api("/kitchen/production", { method: "POST", body: { location_id: loc, lines: ls } }), "Production saved")) draw(el, { location: loc }); };
    el.querySelector("#use").onsubmit = async (e) => { e.preventDefault(); const ls = readLines(e.target); if (!ls.length) return toast("Enter what you used.");
      if (await run(() => api("/kitchen/use", { method: "POST", body: { location_id: loc, lines: ls } }), "Ingredients saved")) draw(el, { location: loc }); };
    const tgt = el.querySelector("#tgt");
    if (tgt) tgt.onsubmit = async (e) => { e.preventDefault(); const f = new FormData(tgt);
      if (await run(() => api("/kitchen/target", { method: "POST", body: { item_id: f.get("item"), qty: f.get("qty") || null, extra: f.get("extra") || null } }), "Target saved")) draw(el, { location: loc }); };
  } },
];
