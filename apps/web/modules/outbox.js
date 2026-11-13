/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// Outbox: every email, WhatsApp and SMS the app sent for this business. Until a provider is set up they are only logged.
import { api } from "/assets/app.js";
import { DataTable, empty, html, icon, kpiRow, openDialog, pageHead, pill } from "/assets/kit/index.js";
import { area, head } from "./lib/areas.js";
import { stamp } from "./lib/format.js";

const CHANNEL = { email: ["Email", "mail", "#2563eb"], whatsapp: ["WhatsApp", "message", "#16a34a"], sms: ["SMS", "phone", "#f59e0b"] };
const TONE = { SENT: "good", DELIVERED: "good", LOGGED: "info", FAILED: "bad", QUEUED: "warn" };

async function outbox(el, q) {
  const { messages } = await api("/outbox");
  const shown = q.channel ? messages.filter((m) => m.channel === q.channel) : messages;
  const logged = messages.some((m) => m.delivery === "LOGGED");
  el.style.setProperty("--area", area("outbox"));
  el.innerHTML = String(html`${pageHead({ ...head("outbox"), title: "Outbox", subtitle: "Purchase orders, stock alerts and other messages the app sent for you." })}
    ${logged ? html`<div class="card k-test">${icon("info")}<div><b>Test mode</b><p class="muted small">No email, WhatsApp or SMS provider is set up yet, so messages are
      written here instead of being sent. Add the provider keys on the server and they go out for real - nothing else changes.</p></div></div>` : ""}
    ${kpiRow(Object.entries(CHANNEL).map(([k, [label, ic, color]]) => ({ label, value: messages.filter((m) => m.channel === k).length, icon: ic, area: color })))}
    <div class="kit-chips"><a class="kit-chip ${q.channel ? "" : "on"}" href="#/outbox">All</a>${Object.entries(CHANNEL).map(([k, [label]]) =>
      html`<a class="kit-chip ${q.channel === k ? "on" : ""}" href="#/outbox?channel=${k}">${label}</a>`)}</div>
    <section class="card k-section">${shown.length ? html`<div class="t"></div>` : empty({ icon: "mail", title: "Nothing sent yet", text: "Send a purchase order to a supplier, or wait for a stock alert." })}</section>`);
  if (!shown.length) return;
  const table = new DataTable({ rows: shown, columns: [
    { key: "at", label: "When", render: (m) => html`${stamp(m.at)}` },
    { key: "channel", label: "Channel", render: (m) => html`${icon(CHANNEL[m.channel]?.[1] || "mail", { size: 15 })} ${CHANNEL[m.channel]?.[0] || m.channel}` },
    { key: "recipient", label: "To" },
    { key: "subject", label: "What", render: (m) => html`<a href="javascript:void 0" data-open="${m.id}">${m.subject || m.template}</a>` },
    { key: "delivery", label: "", render: (m) => html`${pill(m.delivery === "LOGGED" ? "logged" : m.delivery.toLowerCase(), TONE[m.delivery] || "")}` }] });
  table.mount(el.querySelector(".t"));
  el.querySelector(".t").addEventListener("click", (e) => {
    const m = shown.find((x) => x.id === e.target.closest("[data-open]")?.dataset.open);
    if (!m) return;
    e.preventDefault();
    openDialog({ title: m.subject || m.template, body: html`<p class="muted small">${CHANNEL[m.channel]?.[0] || m.channel} to ${m.recipient} · ${stamp(m.at)}</p>
      ${m.error ? html`<p class="bad">${m.error}</p>` : ""}<pre class="k-msg">${m.body}</pre>` });
  });
}

export const routes = [
  { path: "/outbox", nav: "Outbox", key: "x", icon: "mail", area: "outbox", group: "Setup", auth: "staff", tenant: true, perm: "manage_business", render: outbox },
];
