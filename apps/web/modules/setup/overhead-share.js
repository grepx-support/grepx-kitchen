/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// A cost the business pays once for several places (head-office rent, the accountant, a campaign), split over them:
// equally, by their sales that month, or by weights you set. Each place gets its share as a line.
import { html, openDialog } from "/assets/kit/index.js";
import { post } from "./common.js";

export async function shareCost({ places, month, groups, categories }) {
  const box = document.createElement("form");
  box.innerHTML = String(html`<div class="row"><label>Cost<input name="category" list="oh-cats" required placeholder="e.g. Accountant"></label>
      <datalist id="oh-cats">${categories.map((c) => html`<option value="${c.category}">`)}</datalist>
      <label>Counts as<select name="group">${Object.entries(groups).map(([g, l]) => html`<option value="${g}" ${g === "other" ? "selected" : ""}>${l}</option>`)}</select></label>
      <label>Amount for the month<input name="amount" type="number" min="0.01" step="0.01" required></label></div>
    <label>Split<select name="rule"><option value="equal">Equally</option><option value="sales">By each place's sales that month</option><option value="custom">By weights I set</option></select></label>
    <div class="oh-places">${places.map((p) => html`<label class="check"><input type="checkbox" name="pl" value="${p.id}" checked> ${p.name}
      <input name="w_${p.id}" type="number" min="0" step="any" placeholder="weight" class="oh-w"></label>`)}</div><label>Note<input name="note" placeholder="e.g. head office rent"></label>`);
  const weights = () => box.querySelectorAll(".oh-w").forEach((w) => { w.hidden = box.rule.value !== "custom"; });
  box.rule.onchange = weights;
  weights();
  if (await openDialog({ title: `Share a cost - ${month}`, body: box, actions: [{ label: "Cancel", value: "" }, { label: "Split it", value: "ok", primary: true }] }) !== "ok") return false;
  const ids = [...box.querySelectorAll("[name=pl]:checked")].map((i) => i.value);
  return post("/setup/overheads/share", { month, category: box.category.value, group: box.group.value, amount: box.amount.value, rule: box.rule.value,
    note: box.note.value, location_ids: ids, weights: Object.fromEntries(ids.map((i) => [i, box[`w_${i}`].value || 0])) }, "Shared");
}
