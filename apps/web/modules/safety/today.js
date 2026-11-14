/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// Food safety today at one place: every check grouped (temperatures, cooking & cooling, checklists), what is due,
// failures. Out of range asks what was done about it. The standard kitchen checks can be added in one tap.
import { api, run } from "/assets/app.js";
import { empty, html, icon, kpiRow, openDialog, pageHead, tabs } from "/assets/kit/index.js";
import { area, head } from "../lib/areas.js";
import { biz, has } from "../lib/business.js";
import { isKitchen, picker, remember, remembered } from "../lib/place.js";
import { card } from "./cards.js";

export const TABS = [{ id: "today", label: "Today", icon: "check", href: "#/safety" }, { id: "log", label: "Log for inspectors", icon: "clipboard", href: "#/safety/log" }];

async function actionTaken(what) {
  const box = document.createElement("div");
  box.innerHTML = '<label>What was done about it?<input name="a" required placeholder="e.g. moved stock to the other fridge, called the technician"></label>';
  const ok = await openDialog({ title: `Out of range: ${what}`, body: box, actions: [{ label: "Cancel", value: "" }, { label: "Save", value: "ok", primary: true }] });
  return ok ? box.querySelector("input").value.trim() : null;
}

export async function safetyPage(el, q) {
  const b = await biz();
  const site = q.site || remembered(b.locations, isKitchen) || b.locations[0]?.id;   // the kitchen first; any place can be picked
  if (!site) { el.innerHTML = '<div class="card"><p>No places set up yet.</p></div>'; return; }
  remember(site);
  const d = await api(`/safety/day?site_id=${site}`);
  const boss = has("manage_business") || has("manage_people");
  el.style.setProperty("--area", area("safety"));
  el.innerHTML = String(html`${pageHead({ ...head("safety"), title: "Food safety", subtitle: `${d.date} · temperatures and checklists`,
    actions: html`${picker(b.locations, site, () => true, "site", "Place")}${boss ? html` <button class="btn" data-presets>${icon("plus", { size: 15 })} Standard checks</button>` : ""}` })}
    ${tabs(TABS, "today")}${kpiRow([{ label: "Still due today", value: d.due, icon: "clock", area: d.due ? "#f59e0b" : "#16a34a" },
      { label: "Out of range today", value: d.failed, icon: "alert", area: d.failed ? "#e11d48" : "#94a3b8" },
      { label: "Checks", value: d.points.length, icon: "clipboard", area: area("safety") }])}
    ${d.points.length ? [...new Set(d.points.map((p) => p.group || "Checks"))].map((g) => html`<h3 class="sf-group">${g}</h3>
      <div class="sf-grid">${d.points.filter((p) => (p.group || "Checks") === g).map((p) => card(p, boss))}</div>`)
      : empty({ icon: "clipboard", title: "No checks here yet", text: boss ? "Add the standard kitchen checks, then change them to suit." : "Ask the owner to set up the checks." })}`);
  const again = () => safetyPage(el, { site });
  el.querySelector("[data-pick]").onchange = (e) => { remember(e.target.value); safetyPage(el, { site: e.target.value }); };
  el.querySelector("[data-presets]")?.addEventListener("click", async () => { if (await run(() => api("/safety/presets", { method: "POST", body: { site_id: site } }), "Standard checks added")) again(); });
  el.querySelectorAll("[data-point]").forEach((form) => {
    const p = d.points.find((x) => x.point_id === form.dataset.point);
    form.querySelector("[data-remove]")?.addEventListener("click", async () => { if (await run(() => api(`/safety/points/${p.point_id}`, { method: "DELETE" }), "Removed")) again(); });
    form.onsubmit = async (e) => {
      e.preventDefault();
      const body = { point_id: p.point_id };
      if (p.kind === "reading") body.value = form.value.value;
      else { const ticked = new Set([...form.querySelectorAll("[name=item]:checked")].map((c) => c.value)); body.answers = Object.fromEntries((p.questions || []).map((i) => [i, ticked.has(i)])); }
      const bad = p.kind === "reading" ? (p.min != null && Number(body.value) < p.min) || (p.max != null && Number(body.value) > p.max) : Object.values(body.answers).includes(false);
      if (bad) { body.action_taken = await actionTaken(p.name); if (!body.action_taken) return; }
      if (await run(() => api("/safety/record", { method: "POST", body }), bad ? "Recorded - flagged" : "Recorded")) again();
    };
  });
}
