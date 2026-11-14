/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// Home: food safety today across the places - checks still due and anything out of range.
import { api } from "/assets/app.js";
import { html } from "/assets/kit/index.js";
import { area } from "../lib/areas.js";
import { biz, has } from "../lib/business.js";

export default {
  id: "safety", title: "Food safety today", icon: "shield", area: area("safety"), href: "#/safety",
  allowed: () => has("manage_business") || has("kitchen") || has("manage_people"),
  load: async () => {
    const b = await biz();
    const days = await Promise.all(b.locations.map((l) => api(`/safety/day?site_id=${l.id}`).then((d) => ({ ...d, place: l }))));
    return days.filter((d) => d.points.length);
  },
  render: (days) => (days.length ? html`<ul class="sf-home">${days.map((d) => html`<li><a href="#/safety?site=${d.place.id}">${d.place.name}</a>
      <span class="${d.failed ? "bad" : ""}">${d.failed ? `${d.failed} out of range` : ""}</span><span class="${d.due ? "warn" : "ok"}">${d.due ? `${d.due} due` : "all done ✓"}</span></li>`)}</ul>`
    : html`<p class="muted">No checks set up yet - <a href="#/safety">add the standard kitchen checks</a>.</p>`),
};
