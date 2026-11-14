/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// An item's parts, in the item form: "Combo of" (selling one takes these out of stock) and "Breaks into" (one unit gives
// these). Rows of item + quantity; the parts' cost is added up as you type.
import { html, icon } from "/assets/kit/index.js";
import { fmt } from "../lib/format.js";

const row = (items, p = {}) => html`<div class="row pt-row"><select name="pt_item"><option value="">-</option>${items.map((x) =>
  html`<option value="${x.id}" ${x.id === p.item_id ? "selected" : ""}>${x.name} (${x.unit})</option>`)}</select>
  <input name="pt_qty" type="number" min="0" step="any" value="${p.qty ?? ""}" class="k-num" placeholder="qty">
  <button type="button" class="kit-iconbtn" data-pt-del aria-label="Remove">${icon("x", { size: 14 })}</button></div>`;

export const partsBlock = (key, title, help, item, items) => html`<fieldset class="pt" data-parts="${key}"><legend>${title}</legend><p class="muted small">${help}</p>
  <div data-pt-rows>${(item[key] || []).map((p) => row(items.filter((x) => x.id !== item.id), p))}</div>
  <button type="button" class="btn small" data-pt-add>${icon("plus", { size: 14 })} Add part</button> <span class="muted small" data-pt-cost></span></fieldset>`;

export function wireParts(form, item, items) {
  const others = items.filter((x) => x.id !== item.id), cost = Object.fromEntries(items.map((x) => [x.id, Number(x.cost || 0)]));
  form.querySelectorAll("[data-parts]").forEach((box) => {
    const sum = () => { const v = read(box); box.querySelector("[data-pt-cost]").textContent = v.length ? `parts cost ${fmt(v.reduce((a, p) => a + cost[p.item_id] * p.qty, 0))}` : ""; };
    box.querySelector("[data-pt-add]").onclick = () => { box.querySelector("[data-pt-rows]").insertAdjacentHTML("beforeend", String(row(others))); sum(); };
    box.onclick = (e) => { if (e.target.closest("[data-pt-del]")) { e.target.closest(".pt-row").remove(); sum(); } };
    box.oninput = sum;
    sum();
  });
}

const read = (box) => [...box.querySelectorAll(".pt-row")].map((r) => ({ item_id: r.querySelector("[name=pt_item]").value, qty: Number(r.querySelector("[name=pt_qty]").value || 0) }))
  .filter((p) => p.item_id && p.qty > 0);

export const partsOf = (form, key) => read(form.querySelector(`[data-parts="${key}"]`));
