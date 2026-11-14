/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// One check as a card: a reading (type the number, it turns green or red against the safe range) or a checklist
// (tick each item); today's records underneath; what is still due.
import { html, icon, pill } from "/assets/kit/index.js";

const range = (p) => (p.min != null && p.max != null ? `${p.min} to ${p.max}${p.unit}` : p.min != null ? `at least ${p.min}${p.unit}` : `at most ${p.max}${p.unit}`);
const done = (l) => html`<span class="sf-rec ${l.ok ? "ok" : "bad"}" title="${l.by}${l.action_taken ? ` - ${l.action_taken}` : ""}">${l.at.slice(11)}
  ${l.value != null ? html`<b>${l.value}</b>` : l.ok ? "✓" : `✗ ${(l.failed || []).length}`}</span>`;

function reading(p) {
  return html`<div class="sf-read"><input name="value" type="number" step="0.1" inputmode="decimal" placeholder="${p.unit || "value"}"><span class="muted small">safe: ${range(p)}</span></div>`;
}

function checklist(p) {
  return html`<ul class="sf-items">${p.questions.map((i) => html`<li><label class="check"><input type="checkbox" name="item" value="${i}"> ${i}</label></li>`)}</ul>`;
}

export const card = (p, canEdit) => html`<form class="card sf-card ${p.failed_today ? "failed" : p.due ? "due" : "done"}" data-point="${p.point_id}">
  <header><b>${p.name}</b>${p.due ? pill(`${p.due} due`, "warn") : pill("done", "good")}${canEdit ? html`<button type="button" class="btn small sf-x" data-remove title="Remove this check">×</button>` : ""}</header>
  ${p.kind === "reading" ? reading(p) : checklist(p)}
  <div class="sf-today">${p.today.map(done)}</div>
  <button class="btn primary small">${icon("check", { size: 14 })} Record</button></form>`;
