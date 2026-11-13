/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// What the terminal shows, loaded in one go: the week's target per dish, what was made today, and this kitchen's alerts.
import { api } from "/assets/app.js";

export class KitchenFeed {
  constructor(locationId) { this.locationId = locationId; }

  async load() {
    const at = encodeURIComponent(this.locationId);
    const [plan, today, alerts] = await Promise.all([api(`/kitchen/target?location_id=${at}`), api(`/kitchen/today?location_id=${at}`),
      api("/inventory/alerts").catch(() => ({ alerts: [] }))]);
    const made = {};
    today.records.filter((r) => r.kind === "produce").forEach((r) => { made[r.item_name] = (made[r.item_name] || 0) + r.qty; });
    return {
      dishes: plan.lines.map((l) => ({ ...l, made: made[l.name] || 0, left: Math.max(0, (l.target || 0) - (made[l.name] || 0)) }))
        .sort((a, z) => z.left - a.left || a.name.localeCompare(z.name)),
      records: today.records.slice(0, 12),
      alerts: alerts.alerts.filter((a) => a.location_id === this.locationId),
    };
  }

  /** Record a cooked batch: qty in the dish's unit. */
  produce(itemId, qty) {
    return api("/kitchen/production", { method: "POST", body: { location_id: this.locationId, lines: [{ item_id: itemId, qty }] } });
  }
}
