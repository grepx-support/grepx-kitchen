/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// An order's events as a vertical timeline: made, sent, received, billed, approved, paid (or cancelled / voided).
import { html, icon } from "/assets/kit/index.js";

const KIND = { made: ["plus", "#7c3aed"], sent: ["send", "#2563eb"], received: ["inbox", "#0ea5e9"], billed: ["receipt", "#f59e0b"],
  approved: ["check", "#14b8a6"], paid: ["coin", "#16a34a"], cancelled: ["x", "#94a3b8"], void: ["x", "#e11d48"] };

const when = (at) => {
  if (!at) return "";
  if (at.endsWith("T23:59:59")) return new Date(`${at.slice(0, 10)}T00:00:00`).toLocaleDateString();      // a date without a time
  return new Date(at).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
};

export function timelineView(events) {
  if (!events?.length) return html`<p class="muted small">Nothing has happened yet.</p>`;
  return html`<ol class="o-time">${events.map((e) => {
    const [ic, colour] = KIND[e.kind] || ["dot", "#64748b"];
    return html`<li style="--c:${colour}"><span class="o-dot">${icon(ic, { size: 13 })}</span>
      <div><b>${e.title}</b> <span class="muted small">${when(e.at)}${e.who ? ` · ${e.who}` : ""}</span>${e.detail ? html`<div class="muted small">${e.detail}</div>` : ""}</div></li>`;
  })}</ol>`;
}
