/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// Allergen and veg marks as the menu shows them: Indian veg / non-veg squares, short allergen tags with an emoji.
import { html } from "/assets/kit/index.js";

export const ALLERGEN = { gluten: ["🌾", "Gluten"], crustaceans: ["🦐", "Crustaceans"], eggs: ["🥚", "Eggs"], fish: ["🐟", "Fish"],
  peanuts: ["🥜", "Peanuts"], soy: ["🫘", "Soy"], milk: ["🥛", "Milk"], tree_nuts: ["🌰", "Tree nuts"], celery: ["🥬", "Celery"],
  mustard: ["🟡", "Mustard"], sesame: ["⚪", "Sesame"], sulphites: ["🍷", "Sulphites"], lupin: ["🌼", "Lupin"], molluscs: ["🦪", "Molluscs"] };
export const DIET = { vegan: ["Vegan", "#15803d"], veg: ["Veg", "#16a34a"], egg: ["Egg", "#ca8a04"], non_veg: ["Non-veg", "#b91c1c"] };

export const dietMark = (d) => (DIET[d] ? html`<span class="ch-diet" style="--d:${DIET[d][1]}" title="${DIET[d][0]}"><i></i>${DIET[d][0]}</span>`
  : html`<span class="ch-diet unknown" title="Mark the ingredients veg / egg / non-veg in Setup -> Items">?</span>`);
export const allergenTags = (list) => html`${(list || []).map((a) => html`<span class="ch-al" title="${ALLERGEN[a]?.[1] || a}">${ALLERGEN[a]?.[0] || ""} ${ALLERGEN[a]?.[1] || a}</span>`)}`;

/** The fields for Setup -> Items: veg mark and allergen ticks for an ingredient. */
export const itemFields = (i = {}) => html`<label>Veg mark<select name="diet"><option value="">-</option>${Object.entries(DIET).map(([k, [label]]) =>
  html`<option value="${k}" ${i.diet === k ? "selected" : ""}>${label}</option>`)}</select></label>
  <fieldset class="ch-pick"><legend>Allergens</legend>${Object.entries(ALLERGEN).map(([k, [e, label]]) =>
    html`<label class="ch-al-pick"><input type="checkbox" name="al_${k}" ${(i.allergens || []).includes(k) ? "checked" : ""}>${e} ${label}</label>`)}</fieldset>`;
export const pickedAllergens = (form) => Object.keys(ALLERGEN).filter((k) => form.querySelector(`[name=al_${k}]`)?.checked);
