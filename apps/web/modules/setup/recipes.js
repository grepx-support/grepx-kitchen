/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// Recipes: one card per finished product - what a batch makes, and its ingredients dragged in from the palette (KIT-01/02).
import { Builder, h, html } from "/assets/kit/index.js";
import { post } from "./common.js";

export default {
  id: "recipes", label: "Recipes", icon: "pot",
  render(el, s, q, { redraw }) {
    const products = s.items.filter((i) => i.kind === "finished");
    if (!products.length) { el.innerHTML = '<div class="card"><p class="muted">Add finished products under Items first.</p></div>'; return; }
    const names = Object.fromEntries(s.items.map((i) => [i.id, i]));
    const palette = s.items.filter((i) => i.kind !== "finished" && i.active !== false).map((i) => ({ id: i.id, name: i.name, unit: i.unit, category: i.category || i.kind }));
    el.replaceChildren(...products.map((p) => {
      const r = s.recipes.find((x) => x.id === p.id) || {};
      const card = h("section", { class: "card accent k-section" });
      card.innerHTML = String(html`<div class="k-bar"><h2 class="grow">${p.name}</h2><label>One batch makes (${p.unit})<input name="out" type="number" min="0" step="any" value="${r.batch_output ?? ""}"></label>
        <button class="btn primary" data-save>Save recipe</button></div><p class="muted">Ingredients for one batch (optional) - drag them in.</p><div class="slot"></div>`);
      const builder = new Builder({ items: palette, title: "Ingredients", label: "Per batch", step: 0.5,
        lines: (r.ingredients || []).map((x) => ({ item_id: x.item_id, name: names[x.item_id]?.name || x.item_id, unit: names[x.item_id]?.unit || "", qty: x.qty })) });
      builder.mount(card.querySelector(".slot"));
      card.querySelector("[data-save]").onclick = async () => {
        if (await post("/setup/recipes", { item_id: p.id, batch_output: Number(card.querySelector('[name="out"]').value), ingredients: builder.lines() }, "Recipe saved")) redraw();
      };
      return card;
    }));
  },
};
