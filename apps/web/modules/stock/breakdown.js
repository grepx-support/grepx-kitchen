/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// Break down: bulk stock into its parts at one place - pick the item and how many; its usual split is filled in and can be
// changed to what really came out.
import { api, run, toast } from "/assets/app.js";
import { html, icon } from "/assets/kit/index.js";
import { picker } from "../lib/place.js";

export function breakdownCard(b, items, first) {
  const bulk = items.filter((i) => i.breaks_into.length);
  if (!bulk.length) return html`<section class="card k-section" style="--area:#8b5cf6"><h2>${icon("cube")} Break down</h2>
    <p class="muted">Give an item its parts in Setup → Items ("Breaks into", e.g. 1 whole chicken = 2 breasts + 2 thighs + 2 wings) to break it down here.</p></section>`;
  return html`<section class="card accent k-section" style="--area:#8b5cf6" data-bd><h2>${icon("cube")} Break down</h2>
    <p class="muted">Bulk into its parts. The item leaves stock, its parts arrive - value moves, it is not a cost.</p>
    <div class="k-bar">${picker(b.locations, first, () => true, "bdat", "At")}<label>Item<select name="bditem">${bulk.map((i) => html`<option value="${i.id}">${i.name}</option>`)}</select></label>
      <label>How many<input name="bdqty" type="number" min="0" step="any" value="1" class="k-num"></label><button class="btn primary" data-bdgo>Break down</button></div>
    <div class="bd-out" data-bdout></div></section>`;
}

export function wireBreakdown(body, items, done) {
  const box = body.querySelector("[data-bd]");
  if (!box) return;
  const byId = Object.fromEntries(items.map((i) => [i.id, i]));
  const val = (n) => box.querySelector(`[name=${n}]`).value;
  const draw = () => {
    const item = byId[val("bditem")], qty = Number(val("bdqty") || 0);
    box.querySelector("[data-bdout]").innerHTML = String(html`<div class="bd-flow"><span class="bd-chip src">${qty} ${item.unit} ${item.name}</span>${icon("arrow")}
      ${item.breaks_into.map((p) => html`<label class="bd-chip">${byId[p.item_id]?.name || p.item_id}<input data-part="${p.item_id}" type="number" min="0" step="any" class="k-num" value="${+(Number(p.qty) * qty).toFixed(3)}"> ${byId[p.item_id]?.unit || ""}</label>`)}</div>`);
  };
  box.querySelector("[name=bditem]").onchange = draw;
  box.querySelector("[name=bdqty]").oninput = draw;
  draw();
  box.querySelector("[data-bdgo]").onclick = async () => {
    const qty = Number(val("bdqty") || 0);
    if (qty <= 0) return toast("How many to break down?");
    const outputs = [...box.querySelectorAll("[data-part]")].map((i) => ({ item_id: i.dataset.part, qty: i.value }));
    if (await run(() => api("/stock/break-down", { method: "POST", body: { location_id: val("bdat"), lines: [{ item_id: val("bditem"), qty }], outputs } }), "Broken down")) done();
  };
}
