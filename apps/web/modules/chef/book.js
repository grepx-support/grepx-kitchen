/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// Recipe book: every dish as a card - station, times, cost per portion and margin, veg mark, allergens - with filters.
import { api } from "/assets/app.js";
import { empty, html, icon, kpiRow } from "/assets/kit/index.js";
import { allergenTags, dietMark } from "./marks.js";
import { frame, mins, money } from "./common.js";

const tile = async (r) => html`<a class="card ch-card ${r.has_card ? "" : "draft"}" href="#/chef/recipe?id=${r.item_id}">
  <header>${dietMark(r.diet)}<b>${r.name}</b>${r.station ? html`<span class="ch-st">${r.station}</span>` : ""}</header>
  <div class="ch-nums"><span>${icon("clock", { size: 13 })} ${mins((r.prep_min || 0) + (r.cook_min || 0)) || "no times"}</span>
    <span>${await money(r.unit_cost)} / ${r.unit}</span>${r.margin_pct != null ? html`<span class="${r.margin_pct < 60 ? "bad" : "good"}">${r.margin_pct}% margin</span>` : ""}</div>
  <div class="ch-tags">${allergenTags(r.allergens)}</div>
  <footer class="muted small">${r.ingredients} ingredients · ${r.steps ? `${r.steps} steps` : "no method yet"}</footer></a>`;

export async function bookPage(el, q) {
  const { recipes } = await api("/chef/recipes");
  const stations = [...new Set(recipes.map((r) => r.station).filter(Boolean))].sort();
  const shown = recipes.filter((r) => (!q.station || r.station === q.station) && (!q.diet || r.diet === q.diet)
    && (!q.free || !r.allergens.includes(q.free)) && (!q.draft || !r.has_card));
  const body = await frame(el, "book", "Chef", "Recipe cards with method, cost per portion, allergens and veg marks.");
  const chip = (href, on, label) => html`<a class="kit-chip ${on ? "on" : ""}" href="${href}">${label}</a>`;
  body.innerHTML = String(html`${kpiRow([{ label: "Dishes", value: recipes.length, icon: "book", area: "#f97316" },
      { label: "With a method", value: recipes.filter((r) => r.has_card).length, icon: "check", area: "#16a34a" },
      { label: "No method yet", value: recipes.filter((r) => !r.has_card).length, icon: "alert", area: "#e11d48", href: "#/chef?draft=1" },
      { label: "Low margin (<60%)", value: recipes.filter((r) => r.margin_pct != null && r.margin_pct < 60).length, icon: "receipt", area: "#7c3aed" }])}
    <div class="kit-chips">${chip("#/chef", !q.station && !q.diet && !q.free && !q.draft, "All")}${stations.map((s) => chip(`#/chef?station=${s}`, q.station === s, s))}
      ${chip("#/chef?diet=veg", q.diet === "veg", "Veg")}${chip("#/chef?diet=non_veg", q.diet === "non_veg", "Non-veg")}
      ${chip("#/chef?free=gluten", q.free === "gluten", "Gluten-free")}${chip("#/chef?free=milk", q.free === "milk", "Milk-free")}${chip("#/chef?free=tree_nuts", q.free === "tree_nuts", "Nut-free")}</div>
    ${shown.length ? html`<div class="ch-grid">${await Promise.all(shown.map(tile))}</div>` : empty({ icon: "book", title: "No dishes here", text: "Add finished products and their recipes in Setup." })}`);
}
