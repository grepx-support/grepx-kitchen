/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// Suppliers: drag into order; add or edit one with the WhatsApp number orders are sent to (ORD-01).
import { html } from "/assets/kit/index.js";
import { post, sortList, values, wireSort } from "./common.js";

const form = (x = {}) => html`<form class="card accent k-section"><h2>${x.id ? `Edit ${x.name}` : "Add a supplier"}</h2><input type="hidden" name="id" value="${x.id || ""}">
  <div class="row"><label>Name<input name="name" required value="${x.name || ""}"></label><label>Phone / WhatsApp<input name="phone" value="${x.phone || ""}"></label>
    <label>Email<input name="email" type="email" value="${x.email || ""}"></label><label>Contact person<input name="contact" value="${x.contact || ""}"></label></div>
  <label>Notes<textarea name="notes" rows="2">${x.notes || ""}</textarea></label>
  <p><button class="btn primary">Save</button> ${x.id ? html`<a class="btn" href="#/setup?tab=suppliers">New instead</a>` : ""}</p></form>`;

export default {
  id: "suppliers", label: "Suppliers", icon: "truck",
  render(el, s, q) {
    el.innerHTML = String(html`<section class="card"><p class="muted">Drag to set the order suppliers are listed in.</p>
      ${sortList(s.suppliers.map((x) => ({ id: x.id, title: x.name, tag: "🧾", href: `#/setup?tab=suppliers&edit=${x.id}`, sub: [x.phone, x.contact].filter(Boolean).join(" · ") })))}</section>
      ${form(s.suppliers.find((x) => x.id === q.edit))}`);
    wireSort(el, "suppliers");
    el.querySelector("form").onsubmit = async (e) => {
      e.preventDefault();
      const v = values(e.target);
      if (await post("/setup/suppliers", { supplier_id: v.id || undefined, name: v.name, phone: v.phone, email: v.email, contact: v.contact, notes: v.notes }, "Supplier saved")) location.hash = "#/setup?tab=suppliers";
    };
  },
};
