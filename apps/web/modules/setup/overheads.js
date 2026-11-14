/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// Monthly labour, rent and other costs per location - spread equally over the days of the month (COS-07).
import { DataTable, html } from "/assets/kit/index.js";
import { fmt, thisMonth } from "../lib/format.js";
import { post, values } from "./common.js";

export default {
  id: "costs", label: "Monthly costs", icon: "coin",
  render(el, s, q, { redraw }) {
    const name = Object.fromEntries(s.locations.map((l) => [l.id, l.name]));
    el.innerHTML = String(html`<form class="card accent"><p class="muted">Monthly amounts per location; they are spread equally over the days of the month.</p><div class="row">
        <label>Location<select name="loc">${s.locations.map((l) => html`<option value="${l.id}">${l.name}</option>`)}</select></label><label>Month<input name="month" type="month" value="${thisMonth()}"></label>
        <label>Labour<input name="labour" type="number" min="0" step="0.01" required></label><label>Rent<input name="rent" type="number" min="0" step="0.01" required></label>
        <label>Other<input name="other" type="number" min="0" step="0.01" required></label></div><p><button class="btn primary">Save</button></p></form>
      <section class="card k-section"><div class="list"></div></section>`);
    new DataTable({ rows: s.overheads.map((o) => ({ ...o, place: name[o.location_id] || "" })), filter: false, empty: "No monthly costs yet.", columns: [
      { key: "place", label: "Location" }, { key: "month", label: "Month" },
      ...["labour", "rent", "other"].map((k) => ({ key: k, label: k[0].toUpperCase() + k.slice(1), align: "end", render: (o) => html`${fmt(o[k])}` }))] }).mount(el.querySelector(".list"));
    el.querySelector("form").onsubmit = async (e) => {
      e.preventDefault();
      const v = values(e.target);
      if (await post("/setup/overheads", { location_id: v.loc, month: v.month, labour: v.labour, rent: v.rent, other: v.other }, "Saved")) redraw();
    };
  },
};
