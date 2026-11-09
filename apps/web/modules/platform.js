/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// Platform operator (GrepX): set up a new business and its owner's login (Q2).
import { api, esc, run } from "../../app.js";

export const routes = [
  { path: "/platform", nav: "Businesses", auth: "admin", render: async function draw(el) {
    const list = await api("/platform/businesses");
    el.innerHTML = `<h1>Businesses</h1><div class="card"><table><tr><th>Business</th><th>Currency</th><th>Time zone</th><th>Locations</th></tr>
      ${list.map((b) => `<tr><td>${esc(b.name)}</td><td>${esc(b.currency)}</td><td>${esc(b.timezone)}</td><td>${esc(b.locations)}</td></tr>`).join("") || '<tr><td colspan="4" class="muted">None yet.</td></tr>'}</table></div><br>
      <form id="f" class="card"><h2>Set up a new business</h2><div class="row"><div><label>Business name</label><input name="name" required></div>
        <div><label>Currency</label><input name="currency" required maxlength="3" placeholder="AUD"></div><div><label>Time zone</label><input name="timezone" required placeholder="Australia/Sydney"></div></div>
        <h2 style="margin-top:12px">Owner</h2><div class="row"><div><label>Name</label><input name="oname" required></div><div><label>Email (login)</label><input name="email" type="email" required></div>
        <div><label>Phone</label><input name="phone" required placeholder="+61 412 345 678"></div><div><label>Password (8+)</label><input name="password" type="password" minlength="8" required></div></div>
        <p><button class="btn primary">Create business</button></p><p class="muted small">Creates the business, its roles (owner, warehouse, kitchen, closing, delivery) and the owner's login.</p></form>`;
    el.querySelector("#f").onsubmit = async (e) => { e.preventDefault(); const d = new FormData(e.target);
      if (await run(() => api("/platform/businesses", { method: "POST", body: { name: d.get("name"), currency: d.get("currency"), timezone: d.get("timezone"),
        owner: { name: d.get("oname"), email: d.get("email"), phone: d.get("phone"), password: d.get("password") } } }), "Business created")) draw(el); };
  } },
];
