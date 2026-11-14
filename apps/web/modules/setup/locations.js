/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// Locations: drag them into the order they appear everywhere; add or edit one (BUS-02/04, INV-04, CLS-07).
import { html } from "/assets/kit/index.js";
import { resetBiz } from "../lib/business.js";
import { option, post, sortList, values, wireSort } from "./common.js";

const KINDS = ["warehouse", "kitchen", "store", "truck"];
const TAG = { warehouse: "🏬", kitchen: "🍳", store: "🏪", truck: "🚚" };

const form = (l = {}) => html`<form class="card accent k-section"><h2>${l.id ? `Edit ${l.name}` : "Add a location"}</h2><input type="hidden" name="id" value="${l.id || ""}">
  <div class="row"><label>Name<input name="name" required value="${l.name || ""}"></label><label>Type<select name="kind">${option(KINDS, l.kind || "store")}</select></label>
    <label>Days of cover<input name="cover" type="number" min="1" max="60" value="${l.days_of_cover ?? 3}"></label>
    <label>Count every<select name="every">${[1, 3, 7].map((n) => html`<option value="${n}" ${n === (l.count_every_days || 1) ? "selected" : ""}>${n} day(s)</option>`)}</select></label></div>
  <label>Address (for the live map)<input name="address" value="${l.address || ""}"></label>
  <label class="check"><input type="checkbox" name="holding" ${l.holding ? "checked" : ""}> Holds stock for the other locations (warehouse or kitchen storage)</label>
  ${l.id ? html`<label class="check"><input type="checkbox" name="closed" ${l.active === false ? "checked" : ""}> Closed</label>` : ""}
  <p><button class="btn primary">Save</button> ${l.id ? html`<a class="btn" href="#/setup?tab=locations">New instead</a>` : ""}</p></form>`;

export default {
  id: "locations", label: "Locations", icon: "pin",
  render(el, s, q) {
    el.innerHTML = String(html`<section class="card"><p class="muted">Drag to set the order locations appear in pickers and lists.</p>
      ${sortList(s.locations.map((l) => ({ id: l.id, title: l.name, tag: TAG[l.kind] || "📍", off: l.active === false, href: `#/setup?tab=locations&edit=${l.id}`,
        sub: `${l.kind}${l.holding ? " · holds stock" : ""} · ${l.days_of_cover} days cover · count every ${l.count_every_days} day(s)${l.active === false ? " · closed" : ""}` })))}</section>
      ${form(s.locations.find((l) => l.id === q.edit))}`);
    wireSort(el, "locations");
    el.querySelector("form").onsubmit = async (e) => {
      e.preventDefault();
      const v = values(e.target);
      if (await post("/setup/locations", { location_id: v.id || undefined, name: v.name, kind: v.kind, holding: v.holding, address: v.address,
        days_of_cover: Number(v.cover), count_every_days: Number(v.every), active: !v.closed }, "Location saved")) { resetBiz(); location.hash = "#/setup?tab=locations"; }
    };
  },
};
