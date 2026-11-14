/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// Outbox -> Sent: every email, WhatsApp and SMS the app sent for this business, one line per message (its latest try).
// Failed ones are tried again by themselves (5 min, 30 min, 2 h); "Try again now" does not wait.
import { api, run } from "/assets/app.js";
import { DataTable, empty, html, icon, kpiRow, openDialog, pill } from "/assets/kit/index.js";
import { stamp } from "../lib/format.js";
import { CHANNEL, frame } from "./common.js";
import { showDetails } from "../lib/details.js";

const TONE = { SENT: "good", DELIVERED: "good", LOGGED: "info", FAILED: "bad", QUEUED: "warn", SKIPPED: "" };
const word = (m) => (m.delivery === "FAILED" && m.will_retry ? "failed - will retry" : (m.delivery || "").toLowerCase());

function testMode(messages) {
  return messages.some((m) => m.delivery === "LOGGED") ? html`<div class="card k-test">${icon("info")}<div><b>Test mode</b><p class="muted small">No email,
    WhatsApp or SMS provider is set up yet, so messages are written here instead of being sent. The platform operator connects
    them on the Integrations page - nothing else changes.</p></div></div>` : "";
}

async function details(m, again) {
  const failed = m.delivery === "FAILED";
  const choice = await openDialog({ title: m.subject || m.template, body: html`<p class="muted small">${CHANNEL[m.channel]?.[0] || m.channel} to ${m.recipient}
    · ${stamp(m.at)} · try ${m.tries}</p>${m.error ? html`<p class="bad">${m.error}</p>` : ""}<pre class="k-msg">${m.body}</pre>`,
    actions: failed ? [{ label: "Close", value: "" }, { label: "Try again now", value: "retry", primary: true }] : undefined });
  if (choice === "retry" && await run(() => api(`/outbox/${encodeURIComponent(m.id)}/retry`, { method: "POST" }), "Sending again")) again();
}

export async function sent(el, q) {
  const { messages } = await api("/outbox");
  const shown = messages.filter((m) => (!q.channel || m.channel === q.channel) && (!q.failed || m.delivery === "FAILED"));
  const failed = messages.filter((m) => m.delivery === "FAILED").length;
  const body = frame(el, "sent", "Purchase orders, invoices, reminders and stock alerts the app sent for you.");
  const chip = (href, on, label) => html`<a class="kit-chip ${on ? "on" : ""}" href="${href}">${label}</a>`;
  body.innerHTML = String(html`${testMode(messages)}
    ${kpiRow([...Object.entries(CHANNEL).map(([k, [label, ic, color]]) => ({ label, value: messages.filter((m) => m.channel === k).length, icon: ic, area: color })),
      { label: "Failed", value: failed, icon: "alert", area: failed ? "#e11d48" : "#94a3b8", href: "#/outbox?failed=1" }])}
    <div class="kit-chips">${chip("#/outbox", !q.channel && !q.failed, "All")}${Object.entries(CHANNEL).map(([k, [label]]) =>
      chip(`#/outbox?channel=${k}`, q.channel === k, label))}${chip("#/outbox?failed=1", q.failed, `Failed (${failed})`)}</div>
    <section class="card k-section">${shown.length ? html`<div class="t"></div>` : empty({ icon: "mail", title: "Nothing here", text: "Send a purchase order to a supplier, or wait for a stock alert." })}</section>`);
  if (!shown.length) return;
  new DataTable({ onRow: (r) => showDetails(r.subject || r.template || "Message", r, { long: ["body"] }), rows: shown, columns: [
    { key: "at", label: "When", render: (m) => html`${stamp(m.at)}` },
    { key: "channel", label: "Channel", render: (m) => html`${icon(CHANNEL[m.channel]?.[1] || "mail", { size: 15 })} ${CHANNEL[m.channel]?.[0] || m.channel}` },
    { key: "recipient", label: "To" },
    { key: "subject", label: "What", render: (m) => html`<a href="javascript:void 0" data-open="${m.id}">${m.subject || m.template}</a>` },
    { key: "tries", label: "Tries", render: (m) => html`${m.tries > 1 ? String(m.tries) : ""}` },
    { key: "delivery", label: "", render: (m) => html`${pill(word(m), TONE[m.delivery] || "")}` }] }).mount(body.querySelector(".t"));
  body.querySelector(".t").addEventListener("click", (e) => {
    const m = shown.find((x) => x.id === e.target.closest("[data-open]")?.dataset.open);
    if (!m) return;
    e.preventDefault();
    details(m, () => sent(el, q));
  });
}
