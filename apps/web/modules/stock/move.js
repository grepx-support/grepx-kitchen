/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// Transfer stock between locations, and (for those allowed) correct a count with a reason.
import { api, run, toast } from "/assets/app.js";
import { Builder, html, icon } from "/assets/kit/index.js";
import { biz, has } from "../lib/business.js";
import { catalogue } from "../lib/items.js";
import { picker } from "../lib/place.js";
import { frame } from "./common.js";

export async function move(el) {
  const [b, items] = await Promise.all([biz(), catalogue()]);
  const first = b.locations[0]?.id || "", second = b.locations[1]?.id || first;
  const body = frame(el, "move", { title: "Transfer & adjust", subtitle: "Move stock between stores, or correct a counting error." });
  body.innerHTML = String(html`<section class="card accent"><h2>${icon("swap")} Move stock</h2><div class="k-bar">${picker(b.locations, first, () => true, "from", "From")}
      ${picker(b.locations, second, () => true, "to", "To")}<button class="btn primary" data-move>Transfer</button></div><div class="t"></div></section>
    ${has("adjust_stock") ? html`<section class="card accent k-section" style="--area:#e11d48"><h2>${icon("alert")} Adjust stock</h2>
      <p class="muted">Enter the right quantity. A reason is required and kept in the history.</p><div class="k-bar">${picker(b.locations, first, () => true, "at", "At")}
      <label class="grow">Reason<input name="note" minlength="3" placeholder="e.g. miscounted yesterday"></label><button class="btn danger" data-adjust>Adjust</button></div><div class="a"></div></section>` : ""}`);
  const transfer = new Builder({ items, title: "Items", label: "Move" });
  transfer.mount(body.querySelector(".t"));
  const adjust = has("adjust_stock") ? new Builder({ items, title: "Items", label: "Correct qty", empty: "Drag in the item to correct" }) : null;
  if (adjust) adjust.mount(body.querySelector(".a"));
  const val = (name) => body.querySelector(`[name="${name}"]`).value;
  body.querySelector("[data-move]").onclick = async () => {
    const lines = transfer.lines();
    if (!lines.length) return toast("Add what to move.");
    if (await run(() => api("/stock/transfer", { method: "POST", body: { from_location_id: val("from"), to_location_id: val("to"), lines } }), "Moved")) move(el);
  };
  body.querySelector("[data-adjust]")?.addEventListener("click", async () => {
    const lines = adjust.lines(true);
    if (!lines.length) return toast("Add the item to correct.");
    if (val("note").trim().length < 3) return toast("Write the reason.");
    if (await run(() => api("/stock/adjust", { method: "POST", body: { location_id: val("at"), lines, note: val("note") } }), "Adjusted")) move(el);
  });
}
