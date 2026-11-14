/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// Features: everything the app can do, grouped and explained in a line, each switched on or off for the business.
// A feature that is off leaves the menu for everyone and its pages refuse (the data stays; switch it on to have it back).
import { api, run, state } from "/assets/app.js";
import { html, icon } from "/assets/kit/index.js";
import { resetBiz } from "../lib/business.js";

export const FEATURES = [
  ["Kitchen and menu", "chef", [["kitchen", "Kitchen production", "What to make each day, batches, prep lists and the production plan."],
    ["chef", "Recipe cards and allergens", "Recipe cards with steps and pictures, allergens and veg / non-veg marks, kitchen stations."],
    ["forecast", "Demand forecast", "What each place will sell, from its own history, to plan production and orders."]]],
  ["Stock", "box", [["inventory", "Stock and counts", "Stock at every place, transfers, counts, waste, low-stock alerts."],
    ["closing", "Staff closing", "End-of-day counts and sales at each place."],
    ["warehouse", "Warehouse floor", "Lots with expiry dates, bins, pick lists, barcode scanning, the 3-D view."],
    ["delivery", "Delivery runs", "Plan each driver's day, the driver's phone screen, proof of delivery with signatures."]]],
  ["Buying", "cart", [["orders", "Reorder and purchase orders", "Suggested orders, purchase orders sent to suppliers, receiving, approvals."],
    ["purchasing", "Supplier bills", "Bills matched to orders and receipts, price-jump alerts, paying suppliers."]]],
  ["Selling and money", "coin", [["sales", "Customers and invoices", "Invoices, payments, statements, reminders."],
    ["quotes", "Catering quotations", "Quote, then order, then invoice, for events and catering."],
    ["costing", "Costs and profit", "Cost of goods, monthly costs, profit by place and by day."],
    ["funds", "Funds", "Money brought in from partners, investors and loans, put to use, forecast and paid back."]]],
  ["People", "users", [["team", "Team", "People, their documents, positions and sites."], ["roster", "Roster and clock-in", "Shifts, publishing the week, clocking in and out."],
    ["leave", "Leave", "Leave requests, approvals and balances."], ["payroll", "Payroll", "Monthly pay, deductions, payslips sent with the PDF."]]],
  ["Compliance and data", "shield", [["food_safety", "Food safety", "Temperature and cleaning checks with alerts and a log for inspectors."],
    ["import_export", "Import / export", "Bring records in from Excel or CSV and take them out."]]],
];

/** The pages a feature brings (from the app's own routes): a chip each, click to open. */
function pages(key) {
  const seen = new Set();
  const list = (state.routes || []).filter((r) => r.feature === key && !r.path.includes(":") && !seen.has(r.path) && seen.add(r.path));
  const label = (r) => r.nav || r.path.split("/").filter(Boolean).slice(-1)[0].replace(/[-_]/g, " ").replace(/^./, (c) => c.toUpperCase());
  return list.length ? html`<div class="ft-pages">${list.map((r) => html`<a class="ft-page" href="#${r.path}">${icon(r.icon || "dot", { size: 12 })} ${label(r)}</a>`)}</div>` : "";
}

export default {
  id: "features", label: "Features", icon: "settings",
  render(el, s, q, { redraw }) {
    const on = s.business?.modules || {};
    const total = FEATURES.reduce((n, [, , list]) => n + list.length, 0), live = FEATURES.reduce((n, [, , list]) => n + list.filter(([k]) => on[k] !== false).length, 0);
    el.innerHTML = String(html`<div class="card row ft-head"><p class="muted grow">Switch on what your business uses. What is off leaves the menu for everyone; its records are kept.
        Each feature lists the pages it brings - click one to open it.</p><b class="ft-count">${live} / ${total} on</b>
        <input type="search" placeholder="Find a feature or page" data-find></div>
      <form class="grid two">${FEATURES.map(([group, ic, list]) => html`<section class="card ft-group"><h2>${icon(ic)} ${group}</h2>${list.map(([key, name, what]) =>
        html`<div class="ft-row ${on[key] !== false ? "on" : ""}" data-key="${key}"><label class="ft-switch"><input type="checkbox" name="${key}" ${on[key] !== false ? "checked" : ""}><span class="ft-knob"></span></label>
          <div><b>${name}</b><br><small class="muted">${what}</small>${pages(key)}</div></div>`)}</section>`)}</form>
      <section class="card k-section"><h2>${icon("check")} Always on</h2><p class="muted">Setup, Files, API keys, Accounting export, Approvals, Audit trail, Search (Ctrl K).</p></section>`);
    el.querySelector("[data-find]").oninput = (e) => {
      const t = e.target.value.toLowerCase();
      el.querySelectorAll(".ft-row").forEach((r) => { r.hidden = t && !r.textContent.toLowerCase().includes(t); });
      el.querySelectorAll(".ft-group").forEach((g) => { g.hidden = ![...g.querySelectorAll(".ft-row")].some((r) => !r.hidden); });
    };
    el.querySelector("form").addEventListener("change", async (e) => {
      const box = e.target;
      if (await run(() => api("/setup/business", { method: "PATCH", body: { modules: { [box.name]: box.checked } } }), `${box.checked ? "Switched on" : "Switched off"}`)) {
        resetBiz();
        location.reload();                                    // the menu follows the new switches
      } else box.checked = !box.checked;
    });
  },
};
