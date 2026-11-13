/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// Opens an order's full details in place (a slot under its card or row) and closes it again; each order is loaded once.
import { api } from "/assets/app.js";
import { html, icon } from "/assets/kit/index.js";
import { orderSummary } from "./summary.js";

export class Expander {
  constructor(b) { Object.assign(this, { b, cache: new Map() }); }

  load(id) {
    if (!this.cache.has(id)) this.cache.set(id, api(`/orders/${id}`));
    return this.cache.get(id);
  }

  /** Open or close `slot` for order `id`; returns whether it is now open. */
  async toggle(id, slot, host = slot) {
    if (host.classList.toggle("open") === false) { slot.innerHTML = ""; return false; }
    slot.innerHTML = '<div class="kit-skeleton" style="height:120px"></div>';
    try {
      const o = await this.load(id);
      slot.innerHTML = String(html`${orderSummary(o, this.b)}<p class="o-open"><a class="btn small primary" href="#/orders/${id}">${icon("arrow", { size: 14 })} Open the order page</a></p>`);
    } catch (e) {
      slot.innerHTML = String(html`<p class="bad">Couldn't load: ${e.message}</p>`);
    }
    return true;
  }
}
