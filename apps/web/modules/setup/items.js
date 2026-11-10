/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// Items: drag into the order they appear in palettes and lists; add or edit one (COS-01, KIT-01).
import { html } from "/assets/kit/index.js";
import { fmt } from "../lib/format.js";
import { option, post, sortList, values, wireSort } from "./common.js";

const TAG = { ingredient: "🥩", finished: "🌮", supply: "📦" };

const form = (i = {}, suppliers) => html`<form class="card accent k-section"><h2>${i.id ? `Edit ${i.name}` : "Add an item"}</h2><input type="hidden" name="id" value="${i.id || ""}">
  <div class="row"><label>Name<input name="name" required value="${i.name || ""}"></label><label>Type<select name="kind">${option(["ingredient", "finished", "supply"], i.kind || "ingredient")}</select></label>
    <label>Unit<input name="unit" required placeholder="kg, box, each" value="${i.unit || ""}"></label><label>Cost per unit<input name="cost" type="number" min="0" step="0.0001" value="${i.cost ?? ""}"></label>
    <label>Supplier<select name="supplier"><option value="">-</option>${suppliers.map((x) => html`<option value="${x.id}" ${x.id === i.supplier_id ? "selected" : ""}>${x.name}</option>`)}</select></label>
    <label>Category<input name="category" value="${i.category || ""}" placeholder="e.g. Meat, Dry goods"></label></div>
  ${i.id ? html`<label class="check"><input type="checkbox" name="archived" ${i.active === false ? "checked" : ""}> Archived</label>` : ""}
  <p><button class="btn primary">Save</button> ${i.id ? html`<a class="btn" href="#/setup?tab=items">New instead</a>` : ""}</p></form>`;

export default {
  id: "items", label: "Items", icon: "box",
  render(el, s, q) {
    const sup = Object.fromEntries(s.suppliers.map((x) => [x.id, x.name]));
    el.innerHTML = String(html`<section class="card"><p class="muted">Drag to set the order items appear on every screen.</p>
      ${sortList(s.items.map((i) => ({ id: i.id, title: i.name, tag: TAG[i.kind] || "•", off: i.active === false, href: `#/setup?tab=items&edit=${i.id}`,
        sub: `${i.kind} · ${i.unit} · cost ${fmt(i.cost)}${i.category ? ` · ${i.category}` : ""}${sup[i.supplier_id] ? ` · ${sup[i.supplier_id]}` : ""}` })))}</section>
      ${form(s.items.find((i) => i.id === q.edit), s.suppliers)}`);
    wireSort(el, "items");
    el.querySelector("form").onsubmit = async (e) => {
      e.preventDefault();
      const v = values(e.target);
      if (await post("/setup/items", { item_id: v.id || undefined, name: v.name, kind: v.kind, unit: v.unit, cost: Number(v.cost || 0),
        supplier_id: v.supplier, category: v.category, active: !v.archived }, "Item saved")) location.hash = "#/setup?tab=items";
    };
  },
};
