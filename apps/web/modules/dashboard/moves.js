/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// The latest stock movements across the business - a live feel of the day.
import { api } from "/assets/app.js";
import { html } from "/assets/kit/index.js";
import { area } from "../lib/areas.js";
import { has, on } from "../lib/business.js";
import { fmt, time } from "../lib/format.js";

const KIND = { receive: ["inbox", "#14b8a6"], send_out: ["outbox", "#06b6d4"], send_in: ["inbox", "#06b6d4"], transfer_out: ["swap", "#8b5cf6"],
  transfer_in: ["swap", "#8b5cf6"], produce: ["pot", "#f97316"], use: ["pot", "#fb923c"], adjust: ["alert", "#f43f5e"], count: ["clipboard", "#2563eb"] };

export default {
  id: "moves", title: "Latest stock moves", icon: "list", size: "m", area: area("stock"),
  allowed: ({ b }) => has("view_stock") && on(b, "inventory"),
  load: () => api("/stock/movements?limit=8"),
  render: (d) => html`<ul class="k-feed">${d.movements.map((m) => {
    const [, color] = KIND[m.kind] || ["dot", "#64748b"];
    return html`<li style="--c:${color}"><i></i><span class="k-feed-what"><span><b>${m.kind.replace("_", " ")}</b> · ${m.item_name}</span>
      <small>${m.location_name || ""}${m.other_location_name ? ` ↔ ${m.other_location_name}` : ""} · ${m.user_name || ""}</small></span>
      <span class="${m.qty < 0 ? "bad" : "ok"}">${m.qty > 0 ? "+" : ""}${fmt(m.qty)}</span><time>${time(m.at)}</time></li>`;
  })}</ul>${d.movements.length ? "" : html`<p class="muted">No movements yet.</p>`}`,
};
