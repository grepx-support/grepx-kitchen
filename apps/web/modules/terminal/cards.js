/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// One card per dish: how much of this week's target is still to cook, what was made today, and the record buttons.
import { html, icon } from "/assets/kit/index.js";
import { fmt } from "../lib/format.js";

const hhmm = (at) => (at ? new Date(at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) : "");

const ringOf = (done, target) => {
  const p = target ? Math.min(1, done / target) : 0, c = 2 * Math.PI * 44;
  return html`<svg class="t-ring" viewBox="0 0 100 100"><circle r="44" cx="50" cy="50" class="bg"/>
    <circle r="44" cx="50" cy="50" class="fg" stroke-dasharray="${c}" stroke-dashoffset="${c * (1 - p)}"/><text x="50" y="56">${Math.round(p * 100)}%</text></svg>`;
};

export const dishCard = (d) => html`<article class="t-card ${d.left ? "" : "met"}" data-item="${d.item_id}">
  <header>${ringOf(d.made, d.target)}<div><h3>${d.name}</h3>
    <p>${d.target ? html`<b>${fmt(d.left)}</b> ${d.unit} still to cook` : "No target this week"} · ${fmt(d.on_hand)} on hand</p></div></header>
  <div class="t-stats"><span>Made today<b>${fmt(d.made)}</b></span><span>Week target<b>${fmt(d.target)}</b></span><span>Batch<b>${fmt(d.batch_output)} ${d.unit}</b></span></div>
  <div class="t-acts"><button class="t-big" data-batch>${icon("flame", { size: 22 })} +1 batch</button>
    <button class="t-ghost" data-custom aria-label="Record another amount">${icon("plus", { size: 22 })}</button>
    <button class="t-ghost" data-time aria-label="Start a timer for ${d.name}">${icon("clock", { size: 22 })}</button></div></article>`;

export const feed = (records) => records.length ? html`<ul class="t-feed">${records.map((r) => html`<li class="${r.kind}">
  <b>${r.kind === "produce" ? "+" : "−"}${fmt(r.qty)} ${r.unit}</b> ${r.item_name}<small>${hhmm(r.at)} · ${r.by}</small></li>`)}</ul>`
  : html`<p class="t-muted">Nothing recorded yet today.</p>`;

const SAYS = { low: () => "below minimum", expiring: (a) => `use by ${a.expiry}`, expired: () => "expired - throw away", negative: () => "below zero - count it" };

/** One line per item and problem (alerts repeat day after day), scrolling round. */
export function ticker(alerts) {
  const once = [...new Map(alerts.map((a) => [`${a.item_id}:${a.kind}`, a])).values()];
  if (!once.length) return "";
  return html`<div class="t-ticker"><div>${[...once, ...once].map((a) => html`<span class="${a.kind}">
    ${icon(a.kind === "low" ? "trend" : "alert", { size: 16 })} ${a.item_name}: ${(SAYS[a.kind] || (() => a.kind))(a)}</span>`)}</div></div>`;
}
