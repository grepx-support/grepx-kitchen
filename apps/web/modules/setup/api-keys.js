/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// Setup -> API keys: keys for other systems (website, POS, a spreadsheet script). Read keys only look; write keys can
// change things. The full key shows once; revoke any time.
import { api, run, toast } from "/assets/app.js";
import { empty, html, icon, openDialog, pill } from "/assets/kit/index.js";

async function made(key) {
  const box = document.createElement("div");
  box.innerHTML = String(html`<p><b>Copy this key now</b> - it is not shown again.</p><pre class="ak-key">${key.key}</pre>
    <p class="muted small">Send it with every call as the header <code>X-Api-Key</code>. Example:</p>
    <pre class="ak-ex">curl -H "X-Api-Key: ${key.key}" ${location.origin}/api/v1/stock/items</pre>`);
  const copy = () => navigator.clipboard?.writeText(key.key).then(() => toast("Copied"));
  await openDialog({ title: `Key for ${key.name}`, body: box, actions: [{ label: "Copy", value: "copy" }, { label: "Done", value: "", primary: true }] }).then((v) => v === "copy" && copy());
}

export default {
  id: "api", label: "API keys", icon: "lock",
  async render(el, s, q, { redraw }) {
    const d = await api("/setup/api-keys");
    el.innerHTML = String(html`<section class="card accent"><h2>${icon("lock")} Connect other systems</h2>
      <p class="muted">A key lets your website, till or a script use the same data as this app. <a href="/docs" target="_blank">See every call →</a></p>
      <form class="row" data-new><label class="grow">Name<input name="name" required placeholder="e.g. Website orders"></label>
        <label>Can<select name="scope"><option value="read">only read</option><option value="write">read and change</option></select></label>
        <button class="btn primary">${icon("plus", { size: 16 })} Make a key</button></form></section>
      <section class="card k-section">${d.keys.length ? html`<table class="m-view"><thead><tr><th>Name</th><th>Can</th><th>Key</th><th>Made</th><th></th></tr></thead><tbody>
        ${d.keys.map((k) => html`<tr class="${k.active ? "" : "muted"}"><td><b>${k.name}</b></td><td>${pill(k.scope === "write" ? "read and change" : "read", k.scope === "write" ? "warn" : "info")}</td>
          <td><code>gx_${k.key_id}_••••</code></td><td>${String(k.created_at).slice(0, 10)} ${k.created_by ? `by ${k.created_by}` : ""}</td>
          <td class="end">${k.active ? html`<button class="btn small danger" data-revoke="${k.key_id}">Revoke</button>` : pill(`revoked ${String(k.revoked_at).slice(0, 10)}`)}</td></tr>`)}</tbody></table>`
        : empty({ icon: "lock", title: "No keys yet", text: "Make one when another system needs to read or send data." })}</section>`);
    el.querySelector("[data-new]").onsubmit = async (e) => {
      e.preventDefault();
      const key = await run(() => api("/setup/api-keys", { method: "POST", body: { name: e.target.name.value, scope: e.target.scope.value } }));
      if (key) { await made(key); redraw(); }
    };
    el.querySelectorAll("[data-revoke]").forEach((b) => b.onclick = async () => {
      if (confirm("Revoke this key? Anything using it stops working at once.") && await run(() => api(`/setup/api-keys/${b.dataset.revoke}`, { method: "DELETE" }), "Revoked")) redraw();
    });
  },
};
