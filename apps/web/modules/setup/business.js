/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// Business details, which modules are on, and the planning / costing settings (BUS-02/03/06).
import { api, run } from "/assets/app.js";
import { html } from "/assets/kit/index.js";
import { resetBiz } from "../lib/business.js";
import { values } from "./common.js";
import { logoBlock, wireLogo } from "./logo.js";

const MODULES = { kitchen: "Kitchen", inventory: "Inventory", orders: "Reorder and purchase orders", costing: "Costing and sales", closing: "Staff closing" };

export default {
  id: "business", label: "Business", icon: "building",
  render(el, s, q, { redraw }) {
    const b = s.business, st = b.settings || {}, bl = b.billing || {};
    el.innerHTML = String(html`<form class="card accent"><div class="row"><label>Name<input name="name" value="${b.name}"></label>
        <label>Currency<input name="currency" value="${b.currency}" maxlength="3"></label><label>Time zone<input name="timezone" value="${b.timezone}"></label></div>
      <h2 class="k-section">Modules</h2><div class="k-perms">${Object.entries(MODULES).map(([k, v]) => html`<label class="check"><input type="checkbox" name="m_${k}" ${b.modules?.[k] !== false ? "checked" : ""}> ${v}</label>`)}</div>
      <h2 class="k-section">Planning and costing</h2><div class="row">
        <label>Past weeks for targets (1-3)<input name="target_weeks" type="number" min="1" max="3" value="${st.target_weeks}"></label>
        <label>Safety buffer %<input name="safety_pct" type="number" min="0" value="${st.safety_pct}"></label>
        <label>Large change %<input name="large_change_pct" type="number" min="1" value="${st.large_change_pct}"></label>
        <label>COGS range from %<input name="cogs_min" type="number" min="0" max="100" value="${st.cogs_min}"></label>
        <label>to %<input name="cogs_max" type="number" min="0" max="100" value="${st.cogs_max}"></label></div>
      <div class="row"><label>Orders above this need my approval (0 = never)<input name="po_approval_over" type="number" min="0" step="any" value="${st.po_approval_over ?? 0}"></label>
        <label>Tell me when a supplier's price rises by %<input name="price_jump_pct" type="number" min="1" max="500" value="${st.price_jump_pct ?? 10}"></label></div>
      <label>Sales types at closing (comma separated)<input name="sales_types" value="${(st.sales_types || []).join(", ")}"></label>
      ${logoBlock(bl.logo_id)}
      <h2 class="k-section">Invoicing details <span class="muted small">(printed on invoices)</span></h2><div class="row">
        <label>Legal name<input name="legal_name" value="${bl.legal_name || ""}" placeholder="${b.name}"></label>
        <label>Tax name<input name="tax_label" value="${bl.tax_label || ""}" placeholder="GST" maxlength="12"></label>
        <label>Tax registration no.<input name="tax_number" value="${bl.tax_number || ""}"></label>
        <label>Tax rate %<input name="tax_rate" type="number" min="0" max="50" step="any" value="${bl.tax_rate ?? ""}"></label></div>
      <div class="row"><label class="grow">Address<textarea name="address" rows="2">${bl.address || ""}</textarea></label>
        <label class="grow">How to pay (bank, PayNow ...)<textarea name="payment_note" rows="2">${bl.payment_note || ""}</textarea></label></div>
      <label class="check"><input type="checkbox" name="auto_reminders" ${bl.auto_reminders ? "checked" : ""}> Remind customers when an invoice is 1, 7, 14 and 30 days overdue (email by default; channels and words in Outbox → What goes out)</label>
      <p><button class="btn primary">Save</button></p></form>`);
    wireLogo(el, redraw);
    el.querySelector("form").onsubmit = async (e) => {
      e.preventDefault();
      const v = values(e.target);
      const body = { name: v.name, currency: v.currency, timezone: v.timezone, modules: Object.fromEntries(Object.keys(MODULES).map((k) => [k, v[`m_${k}`]])),
        settings: { target_weeks: v.target_weeks, safety_pct: v.safety_pct, large_change_pct: v.large_change_pct, cogs_min: v.cogs_min, cogs_max: v.cogs_max, po_approval_over: v.po_approval_over || 0, price_jump_pct: v.price_jump_pct || 10,
          sales_types: v.sales_types.split(",").map((x) => x.trim()).filter(Boolean) },
        billing: { legal_name: v.legal_name, tax_label: v.tax_label, tax_number: v.tax_number, tax_rate: v.tax_rate || 0, address: v.address, payment_note: v.payment_note, auto_reminders: !!v.auto_reminders } };
      if (await run(() => api("/setup/business", { method: "PATCH", body }), "Saved")) { resetBiz(); redraw(); }
    };
  },
};
