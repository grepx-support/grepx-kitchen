/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// One recipe card: scale it to any number of portions, the method step by step (tick as you go), ingredients with cost
// and allergens, plating and holding; print it for the station wall; edit the card.
import { api, run } from "/assets/app.js";
import { html, icon } from "/assets/kit/index.js";
import { allergenTags, dietMark } from "./marks.js";
import { frame, mins, money } from "./common.js";

const STATIONS = ["prep", "tandoor", "curry", "grill", "fry", "rice", "bakery", "cold", "dessert", "pack"];

function editor(r) {
  return html`<form class="card ch-edit"><h2>${icon("edit")} Edit the card</h2>
    <div class="row"><label>Station<input name="station" list="ch-st" value="${r.station || ""}"><datalist id="ch-st">${STATIONS.map((s) => html`<option value="${s}">`)}</datalist></label>
      <label>Prep (min)<input name="prep_min" type="number" min="0" value="${r.prep_min || ""}"></label><label>Cook per batch (min)<input name="cook_min" type="number" min="0" value="${r.cook_min || ""}"></label>
      <label>Yield after trim / loss %<input name="yield_pct" type="number" min="1" max="100" value="${r.yield_pct || 100}"></label>
      <label>Portion<input name="portion" value="${r.portion || ""}" placeholder="e.g. 250 g bowl"></label><label>Hold for (hours)<input name="hold_hours" type="number" min="0" value="${r.hold_hours || ""}"></label></div>
    <label>Method - one step per line<textarea name="steps" rows="8">${(r.steps || []).join("\n")}</textarea></label>
    <label>Plating<textarea name="plating" rows="2">${r.plating || ""}</textarea></label><label>Chef's notes<textarea name="notes" rows="2">${r.notes || ""}</textarea></label>
    <p><button class="btn primary">${icon("check", { size: 15 })} Save the card</button> <a class="btn" href="#/chef/recipe?id=${r.item_id}">Cancel</a></p></form>`;
}

export async function cardPage(el, q) {
  const { recipe: r } = await api(`/chef/recipes/${encodeURIComponent(q.id)}`);
  const out = Number(r.batch_output || 1), want = Number(q.make || out), k = want / out;
  const body = await frame(el, "book", r.name, `${r.station ? `${r.station} station · ` : ""}${mins(r.prep_min) ? `prep ${mins(r.prep_min)} · ` : ""}${mins(r.cook_min) ? `cook ${mins(r.cook_min)}` : ""}`,
    html`<button class="btn" onclick="print()">${icon("printer", { size: 16 })} Print</button> <a class="btn primary" href="#/chef/recipe?id=${r.item_id}&edit=1">${icon("edit", { size: 16 })} Edit</a>`);
  if (q.edit) {
    body.innerHTML = String(editor(r));
    body.querySelector("form").onsubmit = async (e) => {
      e.preventDefault();
      const f = Object.fromEntries(new FormData(e.target));
      if (await run(() => api(`/chef/recipes/${r.item_id}/card`, { method: "PUT", body: { ...f, steps: f.steps.split("\n") } }), "Card saved")) location.hash = `#/chef/recipe?id=${r.item_id}`;
    };
    return;
  }
  body.innerHTML = String(html`${r.image_id ? html`<img class="ch-photo" src="/api/v1/media/${r.image_id}" alt="">` : ""}<div class="ch-head card">${dietMark(r.diet)}<div class="ch-tags">${allergenTags(r.allergens)}${r.allergens.length ? "" : html`<span class="muted small">No allergens marked on its ingredients</span>`}</div>
      <div class="ch-figs"><span><b>${await money(r.unit_cost)}</b> cost / ${r.unit}</span><span><b>${await money(r.price)}</b> price</span>
        <span class="${r.margin_pct != null && r.margin_pct < 60 ? "bad" : "good"}"><b>${r.margin_pct ?? "-"}%</b> margin</span><span><b>${r.yield_pct || 100}%</b> yield</span>
        ${r.portion ? html`<span><b>${r.portion}</b> portion</span>` : ""}${r.hold_hours ? html`<span><b>${r.hold_hours} h</b> holding</span>` : ""}</div></div>
    <div class="ch-two"><section class="card"><h2>Ingredients</h2><form class="ch-scale">Make <input name="make" type="number" min="0.1" step="any" value="${want}"> ${r.unit} <button class="btn small">Scale</button></form>
        <table class="kit-table"><tr><th>Ingredient</th><th class="num">Qty</th><th class="num">Cost</th><th></th></tr>
        ${r.ingredients.map((i) => html`<tr><td>${i.name}</td><td class="num">${Math.round(i.qty * k * 1000) / 1000} ${i.unit}</td><td class="num">${Math.round(i.cost * k * 100) / 100}</td>
          <td>${allergenTags(i.allergens)}</td></tr>`)}</table><p class="muted small">One batch makes ${out} ${r.unit}.</p></section>
      <section class="card"><h2>Method</h2>${(r.steps || []).length ? html`<ol class="ch-steps">${r.steps.map((s) => html`<li><label><input type="checkbox"> ${s}</label></li>`)}</ol>`
        : html`<p class="muted">No method yet - <a href="#/chef/recipe?id=${r.item_id}&edit=1">write it</a>.</p>`}
        ${r.plating ? html`<h3>Plating</h3><p>${r.plating}</p>` : ""}${r.notes ? html`<h3>Notes</h3><p>${r.notes}</p>` : ""}</section></div>`);
  body.querySelector(".ch-scale").onsubmit = (e) => { e.preventDefault(); location.hash = `#/chef/recipe?id=${r.item_id}&make=${e.target.make.value}`; };
}
