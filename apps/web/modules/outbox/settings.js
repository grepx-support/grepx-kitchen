/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// Outbox -> What goes out: for each message the business sends, whether it goes out by itself, on which channels, and in
// the business's own words ({placeholders} are filled in). Saved for this business only; "Use the default" undoes it.
import { api, run } from "/assets/app.js";
import { html, icon, pill } from "/assets/kit/index.js";
import { CHANNEL, frame } from "./common.js";

function card(m) {
  const now = m.mine || { enabled: true, channels: m.default.channels, subject: "", text: "" };
  const on = (c) => (now.channels || []).includes(c);
  return html`<form class="card ob-msg" data-key="${m.key}">
    <header><b>${m.label}</b>${m.automatic ? pill("goes out by itself", "info") : pill("sent when you press Send", "")}
      ${m.mine ? pill("your own", "good") : ""}</header>
    ${m.automatic ? html`<label class="check"><input type="checkbox" name="enabled" ${now.enabled !== false ? "checked" : ""}> Send this message</label>
      <div class="ob-ch">${Object.entries(CHANNEL).map(([k, [label, ic, color]]) => html`<label class="ob-chip" style="--c:${color}">
        <input type="checkbox" name="ch_${k}" ${on(k) ? "checked" : ""}>${icon(ic, { size: 14 })} ${label}</label>`)}</div>`
      : html`<p class="muted small">Channels are picked each time you send it.</p>`}
    <label>Subject<input name="subject" value="${now.subject || ""}" placeholder="${m.default.subject}"></label>
    <label>Words<textarea name="text" rows="5" placeholder="${m.default.text}">${now.text || ""}</textarea></label>
    <p class="muted small ob-ph">Fill-ins: ${m.placeholders.map((p) => html`<code data-ph="${p}">{${p}}</code>`)}</p>
    <footer><button class="btn primary" value="save">${icon("check", { size: 15 })} Save</button>
      ${m.mine ? html`<button class="btn" value="reset" type="button" data-reset>Use the default</button>` : ""}</footer></form>`;
}

function values(form) {
  const f = new FormData(form);
  return { enabled: f.has("enabled") || !form.querySelector("[name=enabled]"), subject: f.get("subject") || "", text: f.get("text") || "",
    channels: Object.keys(CHANNEL).filter((k) => f.has(`ch_${k}`)) };
}

export async function settings(el) {
  const { messages } = await api("/outbox/settings");
  const body = frame(el, "settings", "Which messages go out, on which channels, and in your own words.");
  body.innerHTML = String(html`<div class="ob-grid">${messages.map(card)}</div>`);
  const again = () => settings(el);
  const save = (key, payload, done) => run(() => api(`/outbox/settings/${key}`, { method: "PUT", body: payload }), done);
  body.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (await save(e.target.dataset.key, values(e.target), "Saved")) again();
  });
  body.addEventListener("click", async (e) => {
    const ph = e.target.closest("[data-ph]");
    if (ph) {                                        // a fill-in clicked: put it where the cursor is in the words
      const box = ph.closest("form").querySelector("textarea");
      box.setRangeText(`{${ph.dataset.ph}}`, box.selectionStart, box.selectionEnd, "end");
      return box.focus();
    }
    const reset = e.target.closest("[data-reset]");
    if (reset && await save(reset.closest("form").dataset.key, { reset: true }, "Back to the default")) again();
  });
}
