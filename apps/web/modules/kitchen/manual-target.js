/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// The owner's override: type a product's target by hand, or add an event week's extra (KIT-10).
import { api, run } from "/assets/app.js";
import { html } from "/assets/kit/index.js";

export const manualTarget = (t) => html`<details class="card k-section"><summary>Set a target by hand / event week extra</summary>
  <form data-target class="k-bar"><label class="grow">Product<select name="item">${t.lines.map((l) => html`<option value="${l.item_id}">${l.name}</option>`)}</select></label>
    <label>Target (empty = calculated)<input name="qty" type="number" inputmode="decimal" min="0" step="any"></label>
    <label>Event extra<input name="extra" type="number" inputmode="decimal" min="0" step="any"></label><button class="btn">Save</button></form></details>`;

export function wireManualTarget(el, again) {
  const form = el.querySelector("[data-target]");
  if (!form) return;
  form.onsubmit = async (e) => {
    e.preventDefault();
    const f = new FormData(form);
    if (await run(() => api("/kitchen/target", { method: "POST", body: { item_id: f.get("item"), qty: f.get("qty") || null, extra: f.get("extra") || null } }), "Target saved")) again();
  };
}
