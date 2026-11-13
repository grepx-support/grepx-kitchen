/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// Business setup by its owner. Each tab is its own file; adding a tab = one more entry in TABS (BUS, ACC, KIT, ORD, COS).
import { api } from "/assets/app.js";
import { html, pageHead, tabs } from "/assets/kit/index.js";
import { area, head } from "./lib/areas.js";
import business from "./setup/business.js";
import items from "./setup/items.js";
import locations from "./setup/locations.js";
import overheads from "./setup/overheads.js";
import { roles, users } from "./setup/people.js";
import recipes from "./setup/recipes.js";
import suppliers from "./setup/suppliers.js";

const TABS = [business, locations, items, suppliers, recipes, users, roles, overheads];

async function setup(el, q) {
  const tab = TABS.find((t) => t.id === q.tab) || TABS[0];
  const s = await api("/setup");
  el.style.setProperty("--area", area("setup"));
  el.innerHTML = String(html`${pageHead({ ...head("setup"), title: "Setup", subtitle: s.business.name })}
    ${tabs(TABS.map((t) => ({ id: t.id, label: t.label, icon: t.icon, href: `#/setup?tab=${t.id}` })), tab.id)}<div class="k-body"></div>`);
  tab.render(el.querySelector(".k-body"), s, q, { redraw: () => setup(el, { tab: tab.id }) });
}

export const routes = [
  { path: "/setup", nav: "Setup", key: "u", icon: "settings", area: "setup", group: "Business", auth: "staff", tenant: true, perm: "manage_business", render: setup },
];
