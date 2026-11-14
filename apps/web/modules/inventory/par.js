/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// Minimum and maximum per item at a location: under the minimum raises an alert; the maximum is what to fill up to.
import { api, run } from "/assets/app.js";
import { html } from "/assets/kit/index.js";
import { biz } from "../lib/business.js";
import { fmt } from "../lib/format.js";
import { picker } from "../lib/place.js";
import { frame } from "./common.js";

export async function par(el, q) {
  const b = await biz();
  const d = await api(`/inventory/par?location_id=${q.location || ""}`);
  const body = frame(el, "par", "Changes save as you leave a box.", picker(b.locations, d.location_id));
  body.innerHTML = String(html`<section class="card"><div class="kit-scroll"><table><thead><tr><th>Item</th><th class="end">On hand</th><th class="end">Minimum</th><th class="end">Maximum</th><th></th></tr></thead>
    <tbody>${d.lines.map((l) => html`<tr data-item="${l.item_id}"><td><b>${l.name}</b> <span class="muted small">${l.unit}</span></td>
      <td class="end ${l.min && l.on_hand < l.min ? "bad" : ""}">${fmt(l.on_hand)}</td>
      <td class="end"><input class="k-num" type="number" min="0" step="any" name="min" value="${l.min ?? ""}" aria-label="Minimum ${l.name}"></td>
      <td class="end"><input class="k-num" type="number" min="0" step="any" name="max" value="${l.max ?? ""}" aria-label="Maximum ${l.name}"></td>
      <td>${l.min && l.on_hand < l.min ? html`<span class="kit-pill bad">low</span>` : ""}</td></tr>`)}</tbody></table></div></section>`);
  el.querySelector("[data-pick]").onchange = (e) => { location.hash = `#/inventory/par?location=${e.target.value}`; };
  body.querySelectorAll("tr[data-item] input").forEach((input) => input.onchange = () => {
    const row = input.closest("tr");
    run(() => api("/inventory/par", { method: "POST", body: { location_id: d.location_id, item_id: row.dataset.item,
      min: row.querySelector("[name=min]").value || 0, max: row.querySelector("[name=max]").value } }), "Saved");
  });
}
