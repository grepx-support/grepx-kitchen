/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// The business logo printed on every document (invoices, orders, payslips, reports): upload, preview, remove.
import { api, run } from "/assets/app.js";
import { html, icon } from "/assets/kit/index.js";
import { resetBiz } from "../lib/business.js";
import { asDataUrl, pickFile } from "../lib/files.js";

export const logoBlock = (logoId) => html`<h2 class="k-section">Logo <span class="muted small">(on every PDF - PNG with a clear background looks best)</span></h2>
  <div class="row k-logo">${logoId ? html`<img src="/api/v1/media/${logoId}" alt="Logo" style="max-height:56px;max-width:220px">` : html`<span class="muted">No logo yet - documents show the business initials.</span>`}
    <button type="button" class="btn small" data-logo>${icon("upload", { size: 15 })} ${logoId ? "Change" : "Upload"}</button>
    ${logoId ? html`<button type="button" class="btn small" data-logo-off>Remove</button>` : ""}</div>`;

export function wireLogo(el, redraw) {
  el.querySelector("[data-logo]")?.addEventListener("click", async () => {
    const file = await pickFile("image/png,image/jpeg,image/webp");
    if (file && await run(async () => api("/setup/logo", { method: "POST", body: { image: await asDataUrl(file) } }), "Logo saved")) { resetBiz(); redraw(); }
  });
  el.querySelector("[data-logo-off]")?.addEventListener("click", async () => {
    if (await run(() => api("/setup/logo", { method: "DELETE" }), "Logo removed")) { resetBiz(); redraw(); }
  });
}
