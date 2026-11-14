/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// What the chef pages share: the frame with its tabs, money and minutes.
import { html, pageHead, tabs } from "/assets/kit/index.js";
import { area, head } from "../lib/areas.js";
import { biz } from "../lib/business.js";

const TABS = [{ id: "book", label: "Recipe book", icon: "book", href: "#/chef" }, { id: "prep", label: "Prep list", icon: "clipboard", href: "#/chef/prep" },
  { id: "allergens", label: "Allergen chart", icon: "alert", href: "#/chef/allergens" }];

export async function frame(el, current, title, subtitle, actions = "") {
  el.style.setProperty("--area", area("chef"));
  el.innerHTML = String(html`${pageHead({ ...head("chef"), title, subtitle, actions })}${tabs(TABS, current)}<div class="k-body"></div>`);
  return el.querySelector(".k-body");
}

export async function money(n) {
  if (n == null) return "-";
  const b = await biz();
  return new Intl.NumberFormat(undefined, { style: "currency", currency: b.business?.currency || "AUD", maximumFractionDigits: 2 }).format(n);
}

export const mins = (m) => (!m ? "" : m < 60 ? `${m} min` : `${Math.floor(m / 60)} h${m % 60 ? ` ${m % 60} min` : ""}`);
