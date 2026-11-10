/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// The warehouse floor's header and tabs.
import { html, pageHead, tabs } from "/assets/kit/index.js";
import { area, head } from "../lib/areas.js";
import { picker } from "../lib/place.js";

export function frame(el, current, b, place, subtitle) {
  el.style.setProperty("--area", area("floor"));
  el.innerHTML = String(html`${pageHead({ ...head("floor"), title: "Warehouse floor", subtitle, actions: picker(b.locations, place, () => true, "location", "Location") })}
    ${tabs([{ id: "lots", label: "Lots & expiry", icon: "clock", href: `#/warehouse?location=${place}` },
      { id: "bins", label: "Bins", icon: "layout", href: `#/warehouse/bins?location=${place}` },
      { id: "picks", label: "Pick lists", icon: "list", href: `#/warehouse/picks?location=${place}` }], current)}<div class="k-body"></div>`);
  return el.querySelector(".k-body");
}

export const tone = (days) => (days === null ? "" : days < 0 ? "bad" : days <= 2 ? "warn" : days <= 7 ? "info" : "good");
export const when = (days) => (days === null ? "no date" : days < 0 ? `expired ${-days}d ago` : days === 0 ? "expires today" : `${days} day${days === 1 ? "" : "s"} left`);
