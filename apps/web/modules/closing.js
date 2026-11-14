/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// Staff closing: few steps - count what you see, enter sales, note issues, check, submit (CLS-01..09).
import { api } from "/assets/app.js";
import { html, icon, pageHead } from "/assets/kit/index.js";
import { openPdf } from "./money/common.js";
import { area, head } from "./lib/areas.js";
import { biz } from "./lib/business.js";
import { picker, remember, remembered } from "./lib/place.js";
import { ClosingWizard } from "./closing/wizard.js";

const sells = (l) => !l.holding || l.kind !== "warehouse";

async function closing(el, q) {
  const b = await biz();
  const loc = q.location || remembered(b.locations, sells);
  el.style.setProperty("--area", area("closing"));
  if (!loc) { el.innerHTML = '<div class="card"><p>No location set up yet.</p></div>'; return; }
  remember(loc);
  const f = await api(`/closing/form?location_id=${loc}`);
  el.innerHTML = String(html`${pageHead({ ...head("closing"), title: "Closing", subtitle: `${f.location.name} · counts every ${f.location.count_every_days} day(s)${f.last_closing ? ` · last ${f.last_closing}` : ""}`,
    actions: html`${picker(b.locations, loc, sells)} <button class="btn" data-sheet>${icon("printer", { size: 15 })} Count sheet</button>` })}<div class="k-body"></div>`);
  el.querySelector("[data-pick]").onchange = (e) => closing(el, { location: e.target.value });
  el.querySelector("[data-sheet]").onclick = () => openPdf(`/pdf/count-sheet?location_id=${loc}`);
  const body = el.querySelector(".k-body");
  if (f.submitted_today) {
    body.innerHTML = String(html`<section class="card k-done">${icon("check", { size: 54 })}<h2>Done for today</h2><p>${f.location.name} was closed on ${f.date}. Thank you!</p></section>`);
    return;
  }
  new ClosingWizard({ form: f, location: loc, onDone: () => closing(el, { location: loc }) }).mount(body);
}

export const routes = [
  { path: "/closing", feature: "closing", nav: "Closing", key: "c", icon: "clipboard", area: "closing", group: "Daily", auth: "staff", tenant: true, perm: "closing", render: closing },
];
