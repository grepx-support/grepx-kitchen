/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// This week's production target at the first kitchen, against what is on hand.
import { api } from "/assets/app.js";
import { barList, html } from "/assets/kit/index.js";
import { area } from "../lib/areas.js";
import { has, on } from "../lib/business.js";
import { isKitchen, remembered } from "../lib/place.js";

export default {
  id: "target", title: "Kitchen target", icon: "pot", size: "m", area: area("kitchen"),
  allowed: ({ b }) => (has("kitchen") || has("manage_business")) && on(b, "kitchen") && b.locations.some(isKitchen),
  load: async ({ b }) => ({ t: await api(`/kitchen/target?location_id=${remembered(b.locations, isKitchen)}`), place: b.locations.find((l) => l.id === remembered(b.locations, isKitchen)) }),
  render: ({ t, place }) => html`<p class="muted">${place?.name || ""} · week of ${t.week}</p>
    ${barList({ unit: "", empty: "No products yet", rows: t.lines.map((l) => ({ label: `${l.name} (${l.unit})`, value: l.on_hand || 0, marker: l.target,
      note: l.target == null ? "no target yet" : `target ${l.target} · ${l.batches ?? "–"} batches`, color: area("kitchen") })) })}
    <p><a class="btn small" href="#/kitchen">Open kitchen</a></p>`,
};
