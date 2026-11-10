/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// Platform operator (GrepX): every business on the platform, and setting up a new one with its owner's login (Q2).
import { api, run } from "/assets/app.js";
import { html, kpiRow, pageHead } from "/assets/kit/index.js";
import { area, head } from "./lib/areas.js";

async function platform(el) {
  const list = await api("/platform/businesses");
  el.style.setProperty("--area", area("platform"));
  el.innerHTML = String(html`${pageHead({ ...head("platform"), title: "Businesses", subtitle: "Every business on the platform. Each one sees only its own data." })}
    ${kpiRow([{ label: "Businesses", value: list.length, icon: "building", area: area("platform") },
      { label: "Locations", value: list.reduce((a, b) => a + (b.locations || 0), 0), icon: "pin", area: area("stock") }])}
    <div class="grid">${list.map((b) => html`<article class="card accent"><h2>${b.name}</h2><p class="muted">${b.currency} · ${b.timezone}</p><span class="badge">${b.locations} locations</span></article>`)}</div>
    <form class="card accent k-section"><h2>Set up a new business</h2><div class="row"><label>Business name<input name="name" required></label>
        <label>Currency<input name="currency" required maxlength="3" placeholder="AUD"></label><label>Time zone<input name="timezone" required placeholder="Australia/Sydney"></label></div>
      <h2 class="k-section">Owner</h2><div class="row"><label>Name<input name="oname" required></label><label>Email (login)<input name="email" type="email" required></label>
        <label>Phone<input name="phone" required placeholder="+61 412 345 678"></label><label>Password (8+)<input name="password" type="password" minlength="8" required></label></div>
      <p><button class="btn primary">Create business</button></p><p class="muted small">Creates the business, its roles (owner, warehouse, kitchen, closing, delivery) and the owner's login.</p></form>`);
  el.querySelector("form").onsubmit = async (e) => {
    e.preventDefault();
    const d = new FormData(e.target);
    if (await run(() => api("/platform/businesses", { method: "POST", body: { name: d.get("name"), currency: d.get("currency"), timezone: d.get("timezone"),
      owner: { name: d.get("oname"), email: d.get("email"), phone: d.get("phone"), password: d.get("password") } } }), "Business created")) platform(el);
  };
}

export const routes = [
  { path: "/platform", nav: "Businesses", icon: "building", area: "platform", group: "Platform", auth: "admin", render: platform },
];
