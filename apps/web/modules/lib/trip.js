/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// One trip from the warehouse, opened from any board: where it goes, what is on it, its run and driver, who received
// it - with the delivery note PDF and a way to its run.
import { api } from "/assets/app.js";
import { html, icon, openDialog, pill } from "/assets/kit/index.js";
import { openPdf } from "../money/common.js";
import { time } from "./format.js";

export async function showTrip(id) {
  const t = await api(`/stock/deliveries/${encodeURIComponent(id)}`);
  const s = t.stop, r = t.run;
  const body = html`<dl class="kit-facts"><dt>From</dt><dd>${t.from}</dd><dt>To</dt><dd><b>${t.to}</b><br><span class="muted small">${t.to_address || ""}</span></dd>
      <dt>Sent</dt><dd>${t.date} by ${t.by || "-"}</dd><dt>Run</dt><dd>${r ? html`<a href="#/runs/${r.run_id}">${r.name}</a> · ${r.driver_name || "no driver"} · ${r.vehicle || ""} ${pill(r.state.replace("_", " "), "info")}` : "not on a run yet"}</dd>
      ${s?.eta ? html`<dt>ETA</dt><dd>${s.eta}</dd>` : ""}${s?.receiver ? html`<dt>Received by</dt><dd>${s.receiver} at ${time(s.delivered_at)}</dd>` : ""}
      ${s?.reason ? html`<dt>Not delivered</dt><dd class="bad">${s.reason}</dd>` : ""}</dl>
    <table class="m-view"><thead><tr><th>Item</th><th class="end">Qty</th></tr></thead><tbody>${t.lines.map((l) => html`<tr><td>${l.item_name}</td><td class="end">${l.qty} ${l.unit}</td></tr>`)}</tbody></table>`;
  const go = await openDialog({ title: `Trip to ${t.to}`, body, actions: [{ label: "Close", value: "" }, ...(r ? [{ label: "Open the run", value: "run" }] : []),
    { label: "Delivery note", value: "pdf", primary: true }] });
  if (go === "run") location.hash = `#/runs/${r.run_id}`;
  if (go === "pdf") openPdf(`/pdf/delivery/${encodeURIComponent(id)}`);
}
