/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// Allergen chart: every dish against the 14 allergens, with its veg mark - print it for the front of house.
import { api } from "/assets/app.js";
import { html, icon } from "/assets/kit/index.js";
import { ALLERGEN, dietMark } from "./marks.js";
import { frame } from "./common.js";

export async function allergenPage(el) {
  const { allergens, dishes } = await api("/chef/allergens");
  const body = await frame(el, "allergens", "Allergen chart", "From each dish's ingredients - keep the ingredients' marks right in Setup -> Items.",
    html`<button class="btn" onclick="print()">${icon("printer", { size: 16 })} Print</button>`);
  body.innerHTML = String(html`<section class="card ch-chart"><table class="kit-table"><thead><tr><th>Dish</th><th></th>${allergens.map((a) =>
      html`<th class="ch-rot" title="${ALLERGEN[a]?.[1]}"><span>${ALLERGEN[a]?.[0]} ${ALLERGEN[a]?.[1] || a}</span></th>`)}</tr></thead>
    <tbody>${dishes.map((d) => html`<tr><td><a href="#/chef/recipe?id=${d.item_id}">${d.name}</a></td><td>${dietMark(d.diet)}</td>${allergens.map((a) =>
      html`<td class="ch-x">${d.allergens.includes(a) ? "●" : ""}</td>`)}</tr>`)}</tbody></table></section>`);
}
