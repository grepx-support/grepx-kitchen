/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// Items: drag into the order they appear in palettes and lists; add or edit one (COS-01, KIT-01).
import { html, icon } from "/assets/kit/index.js";
import { asDataUrl, pickFile } from "../lib/files.js";
import { fmt } from "../lib/format.js";
import { partsBlock, partsOf, wireParts } from "./parts.js";
import { option, post, sortList, values, wireSort } from "./common.js";
import { itemFields, pickedAllergens } from "../chef/marks.js";

const TAG = { ingredient: "🥩", finished: "🌮", supply: "📦" };

const form = (i = {}, suppliers, items = []) => html`<form class="card accent k-section"><h2>${i.id ? `Edit ${i.name}` : "Add an item"}</h2><input type="hidden" name="id" value="${i.id || ""}">
  <div class="row"><label>Name<input name="name" required value="${i.name || ""}"></label><label>Type<select name="kind">${option(["ingredient", "finished", "supply"], i.kind || "ingredient")}</select></label>
    <label>Unit<input name="unit" required placeholder="kg, box, each" value="${i.unit || ""}"></label><label>Cost per unit<input name="cost" type="number" min="0" step="0.0001" value="${i.cost ?? ""}"></label>
    <label>Sells for (per unit)<input name="price" type="number" min="0" step="0.01" value="${i.price || ""}" placeholder="for invoices"></label>
    <label>Supplier<select name="supplier"><option value="">-</option>${suppliers.map((x) => html`<option value="${x.id}" ${x.id === i.supplier_id ? "selected" : ""}>${x.name}</option>`)}</select></label>
    <label>Category<input name="category" value="${i.category || ""}" placeholder="e.g. Meat, Dry goods"></label>
    <label>Shelf life (days)<input name="shelf_life_days" type="number" min="0" step="1" value="${i.shelf_life_days ?? ""}" placeholder="sets expiry when received"></label>
    <label>Barcode<input name="barcode" value="${i.barcode || ""}" placeholder="for the scanner" maxlength="40"></label></div>
  <div class="row">${itemFields(i)}</div>
  <div class="grid two">${partsBlock("components", "Combo of", "A meal box or kit: selling one takes these out of stock.", i, items)}
    ${partsBlock("breaks_into", "Breaks into", "One unit gives these (whole chicken → breasts, thighs, wings). Used by Stock → Break down.", i, items)}</div>
  ${i.id ? html`<label class="check"><input type="checkbox" name="archived" ${i.active === false ? "checked" : ""}> Archived</label>` : ""}
  <p><button class="btn primary">Save</button> ${i.id ? html`<a class="btn" href="#/setup?tab=items">New instead</a>` : ""}</p></form>`;

/** The item's picture (shown on the item list, recipe cards and orders): upload, change, remove. */
const pictureBlock = (i) => html`<section class="card k-section k-pic"><h2>Picture of ${i.name || "the item"}</h2><div class="row">
  ${i.image_id ? html`<img src="/api/v1/media/${i.image_id}" alt="${i.name}" style="max-height:120px;border-radius:10px">` : html`<span class="muted">No picture yet.</span>`}
  <button type="button" class="btn small" data-pic>${icon("upload", { size: 15 })} ${i.image_id ? "Change" : "Add a picture"}</button>
  ${i.image_id ? html`<button type="button" class="btn small" data-pic-off>Remove</button>` : ""}</div></section>`;

function wirePicture(el, id) {
  el.querySelector("[data-pic]")?.addEventListener("click", async () => {
    const file = await pickFile("image/png,image/jpeg,image/webp");
    if (file && await post(`/setup/items/${id}/picture`, { image: await asDataUrl(file) }, "Picture saved")) location.reload();
  });
  el.querySelector("[data-pic-off]")?.addEventListener("click", async () => {
    if (await post(`/setup/items/${id}/picture`, { remove: true }, "Picture removed")) location.reload();
  });
}

/** How the item's cost moved: each change with what it was and where it came from (a bill with landed costs, an edit). */
function costHistory(item) {
  const h = item.cost_history || [];
  if (!h.length) return "";
  return html`<section class="card k-section"><h2>${icon("chart")} Cost history</h2><table class="m-view"><thead><tr><th>When</th><th>From</th><th class="end">Was</th><th class="end">Now</th><th class="end">Change</th></tr></thead>
    <tbody>${h.map((x) => { const d = x.was ? ((x.cost - x.was) / x.was) * 100 : 0;
      return html`<tr><td>${String(x.at).slice(0, 10)}</td><td>${x.source}</td><td class="end">${fmt(x.was)}</td><td class="end"><b>${fmt(x.cost)}</b></td>
        <td class="end ${d > 0 ? "bad" : "good"}">${d ? `${d > 0 ? "+" : ""}${d.toFixed(1)}%` : ""}</td></tr>`; })}</tbody></table></section>`;
}

export default {
  id: "items", label: "Items", icon: "box",
  render(el, s, q) {
    const sup = Object.fromEntries(s.suppliers.map((x) => [x.id, x.name]));
    el.innerHTML = String(html`<section class="card"><p class="muted">Drag to set the order items appear on every screen.</p>
      ${sortList(s.items.map((i) => ({ id: i.id, title: i.name, tag: TAG[i.kind] || "•", img: i.image_id, off: i.active === false, href: `#/setup?tab=items&edit=${i.id}`,
        sub: `${i.kind} · ${i.unit} · cost ${fmt(i.cost)}${i.category ? ` · ${i.category}` : ""}${sup[i.supplier_id] ? ` · ${sup[i.supplier_id]}` : ""}` })))}</section>
      ${q.edit ? pictureBlock(s.items.find((i) => i.id === q.edit) || {}) : ""}${q.edit ? costHistory(s.items.find((i) => i.id === q.edit) || {}) : ""}${form(s.items.find((i) => i.id === q.edit), s.suppliers, s.items)}`);
    wireSort(el, "items");
    wirePicture(el, q.edit);
    wireParts(el.querySelector("form"), s.items.find((i) => i.id === q.edit) || {}, s.items);
    el.querySelector("form").onsubmit = async (e) => {
      e.preventDefault();
      const v = values(e.target);
      if (await post("/setup/items", { item_id: v.id || undefined, name: v.name, kind: v.kind, unit: v.unit, cost: Number(v.cost || 0), price: Number(v.price || 0),
        supplier_id: v.supplier, category: v.category, active: !v.archived,
        shelf_life_days: v.shelf_life_days === "" ? null : Number(v.shelf_life_days), barcode: v.barcode,
        diet: v.diet || "", allergens: pickedAllergens(e.target),
        components: partsOf(e.target, "components"), breaks_into: partsOf(e.target, "breaks_into") }, "Item saved")) location.hash = "#/setup?tab=items";
    };
  },
};
