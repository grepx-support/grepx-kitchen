/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// What the outbox pages share: channel names and colours, the page frame with its tabs.
import { html, pageHead, tabs } from "/assets/kit/index.js";
import { area, head } from "../lib/areas.js";

export const CHANNEL = { email: ["Email", "mail", "#2563eb"], whatsapp: ["WhatsApp", "message", "#16a34a"], sms: ["SMS", "phone", "#f59e0b"] };

const TABS = [{ id: "sent", label: "Sent", icon: "mail", href: "#/outbox" },
  { id: "settings", label: "What goes out", icon: "settings", href: "#/outbox/settings" }];

export function frame(el, current, subtitle) {
  el.style.setProperty("--area", area("outbox"));
  el.innerHTML = String(html`${pageHead({ ...head("outbox"), title: "Outbox", subtitle })}${tabs(TABS, current)}<div class="k-body"></div>`);
  return el.querySelector(".k-body");
}
