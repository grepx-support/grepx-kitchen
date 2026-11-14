/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// "Throw away" from any screen: how much and why. Waste counts in the cost of goods and in the waste report.
import { api, run } from "/assets/app.js";
import { h, html, openDialog } from "/assets/kit/index.js";

export const REASONS = [["expired", "Expired"], ["spoiled", "Spoiled"], ["damaged", "Damaged"], ["overproduced", "Made too much"], ["other", "Other"]];

/** Ask and record; resolves true when it was recorded. */
export async function waste({ location_id, item_id, name, unit, qty = "", lot_id = "", reason = "expired" }) {
  const form = h("div");
  form.innerHTML = String(html`<p>${name}</p><div class="row"><label>How much (${unit})<input name="qty" type="number" min="0" step="any" value="${qty}"></label>
    <label>Why<select name="reason">${REASONS.map(([v, t]) => html`<option value="${v}" ${v === reason ? "selected" : ""}>${t}</option>`)}</select></label></div>
    <label>Note (optional)<input name="note"></label>`);
  const go = await openDialog({ title: "Throw away", body: form, actions: [{ label: "Back", value: "" }, { label: "Record waste", value: "yes", danger: true }] });
  if (go !== "yes") return false;
  const q = Number(form.querySelector("[name=qty]").value);
  if (!(q > 0)) return false;
  return !!(await run(() => api("/stock/waste", { method: "POST", body: { location_id, reason: form.querySelector("[name=reason]").value,
    note: form.querySelector("[name=note]").value, lines: [{ item_id, qty: q, ...(lot_id ? { lot_id } : {}) }] } }), "Waste recorded"));
}
