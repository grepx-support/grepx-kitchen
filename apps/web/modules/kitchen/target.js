/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// This week's target as one card per product (target, batches, on hand), and the ingredients the target needs.
import { barList, html, pill, progress } from "/assets/kit/index.js";
import { fmt } from "../lib/format.js";

export const targetCards = (t) => html`<div class="k-targets">${t.lines.map((l) => html`<article class="k-target">
    <h3>${l.name}<span>${l.source === "manual" ? pill("set by hand", "info") : ""}${l.extra ? pill(`+${fmt(l.extra)} event`, "warn") : ""}</span></h3>
    <div class="num">${l.target === null ? "–" : fmt(l.target)}<small> ${l.unit} target</small></div>
    ${l.target ? progress(l.on_hand || 0, l.target, { label: `${l.name} on hand against target` }) : ""}
    <div class="meta">${pill(`${l.batches ?? "–"} batches${l.batch_output ? ` × ${fmt(l.batch_output)}` : ""}`)}${pill(`on hand ${fmt(l.on_hand)}`, "info")}</div></article>`)}</div>`;

export const ingredients = (t) => t.ingredients.length ? barList({ rows: t.ingredients.map((i) => ({ label: `${i.name} (${i.unit})`, value: i.on_hand || 0,
  marker: i.needed, color: i.to_buy ? "#e11d48" : "#16a34a", note: i.to_buy ? `needs ${fmt(i.needed)} · buy ${fmt(i.to_buy)}` : `needs ${fmt(i.needed)} · covered` })) }) : "";

export const history = (t) => (t.has_history ? html`<p class="muted">From the last ${t.history_days} days of usage, plus safety buffer, minus stock on hand.</p>`
  : html`<p class="kit-pill warn">No usage history yet - the owner types this week's target by hand.</p>`);
