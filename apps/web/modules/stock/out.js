/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// Warehouse out: the suggested lines for the chosen location are already in the basket; drag in more, change, send.
import { api, run, toast } from "/assets/app.js";
import { Builder, html, icon } from "/assets/kit/index.js";
import { biz } from "../lib/business.js";
import { fmt } from "../lib/format.js";
import { catalogue } from "../lib/items.js";
import { isHolding, notHolding, picker, remember, remembered } from "../lib/place.js";
import { frame } from "./common.js";

export async function warehouseOut(el, q) {
  const b = await biz();
  const to = q.to || remembered(b.locations, notHolding);
  const from = b.locations.find(isHolding)?.id;
  const body = frame(el, "out", { title: "Warehouse out", subtitle: "Send stock from the holding place to a kitchen, store or truck." });
  if (!to || !from) { body.innerHTML = '<div class="card"><p>Set up a holding place and at least one other location first.</p></div>'; return; }
  const [plan, items, held] = await Promise.all([api(`/stock/warehouse-out?to_location_id=${to}`), catalogue(), api(`/stock?location_id=${from}`)]);
  const at = Object.fromEntries(held.levels.map((l) => [l.item_id, l.qty]));
  body.innerHTML = String(html`<div class="card accent"><div class="k-bar">${pickers(b, plan.from_location_id || from, to)}
      <button class="btn primary" data-send>${icon("send", { size: 16 })} Send stock</button></div>
    <p class="muted">Suggested: enough for <b>${plan.days_of_cover}</b> days${plan.has_history ? ` (from ${plan.history_days} days of usage)` : " - no usage history yet, drag items in"}.</p>
    <div class="slot"></div></div>`);
  const builder = new Builder({ title: "Warehouse stock", label: "Send",
    items: items.map((i) => ({ ...i, hint: `warehouse ${fmt(at[i.id] || 0)} ${i.unit}` })),
    lines: plan.lines.map((l) => ({ item_id: l.item_id, name: l.name, unit: l.unit, qty: l.suggested ?? "", hint: `there ${fmt(l.at_location)} · warehouse ${fmt(l.at_holding)}` })) });
  builder.mount(body.querySelector(".slot"));
  body.querySelector('[name="to"]').onchange = (e) => { remember(e.target.value); location.hash = `#/stock/out?to=${e.target.value}`; };
  body.querySelector("[data-send]").onclick = async () => {
    const lines = builder.lines();
    if (!lines.length) return toast("Nothing to send.");
    const sent = await run(() => api("/stock/send", { method: "POST", body: { from_location_id: body.querySelector('[name="from"]').value, to_location_id: to, lines } }), "Sent - it's on the delivery board");
    if (sent) warehouseOut(el, { to });
  };
}

const pickers = (b, from, to) => html`${picker(b.locations, from, isHolding, "from", "From")}${picker(b.locations, to, notHolding, "to", "To")}`;
