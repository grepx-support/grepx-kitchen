/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// The kitchen terminal: a full-screen, touch-first screen for the wall tablet. Composes the feed (data), the dish cards,
// the timers and the number pad; it owns only the layout, the refresh loop and the screen wake lock.
import { api, run, state, store } from "/assets/app.js";
import { avatar, html, icon } from "/assets/kit/index.js";
import { biz } from "../lib/business.js";
import { fmt } from "../lib/format.js";
import { dishCard, feed, ticker } from "./cards.js";
import { KitchenFeed } from "./data.js";
import { burst } from "./fx.js";
import { numpad } from "./numpad.js";
import { TimerBoard } from "./timers.js";

const REFRESH_MS = 45000;

class Terminal {
  constructor(el, kitchens, locationId) {
    Object.assign(this, { el, kitchens, feed: new KitchenFeed(locationId), locationId });
    this.loops = [];
  }

  async start() {
    this.el.innerHTML = String(this.frame());
    this.timers = new TimerBoard(store, this.el.querySelector("[data-timers]"));
    this.timers.draw();
    this.wire();
    await this.refresh();
    this.loops.push(setInterval(() => this.refresh(), REFRESH_MS), setInterval(() => this.clock(), 1000));
    this.clock();
    this.awake();
    window.addEventListener("hashchange", () => this.stop(), { once: true });
  }

  stop() { this.loops.forEach(clearInterval); this.timers?.stop(); this.lock?.release?.(); }

  frame() {
    const me = state.me || {};
    return html`<div class="t-screen"><header class="t-top">
      <a class="t-brand" href="#/kitchen" title="Back to the app">${icon("pot", { size: 22 })}<span>Kitchen terminal</span></a>
      <select data-place aria-label="Kitchen">${this.kitchens.map((k) => html`<option value="${k.id}" ${k.id === this.locationId ? "selected" : ""}>${k.name}</option>`)}</select>
      <time data-clock></time><span class="t-who">${avatar(me.name || "?", { photo: me.photo_id, size: 40, status: "on" })}<b>${(me.name || "").split(" ")[0]}</b></span>
      <button class="t-icon" data-full aria-label="Full screen">${icon("expand", { size: 20 })}</button>
      <a class="t-icon" href="#/kitchen" aria-label="Exit terminal">${icon("logout", { size: 20 })}</a></header>
      <div data-ticker></div>
      <main class="t-main"><section class="t-cards" data-cards><div class="kit-skeleton"></div></section>
        <aside class="t-side"><section><h2>${icon("clock")} Timers</h2><div data-timers></div></section>
          <section><h2>${icon("list")} Today</h2><div data-feed></div></section></aside></main></div>`;
  }

  wire() {
    this.el.querySelector("[data-place]").onchange = (e) => { location.hash = `#/terminal?location=${e.target.value}`; };
    this.el.querySelector("[data-full]").onclick = () => (document.fullscreenElement ? document.exitFullscreen() : document.documentElement.requestFullscreen?.());
    this.el.querySelector("[data-cards]").onclick = (e) => this.onCard(e);
  }

  async refresh() {
    try { this.data = await this.feed.load(); } catch (e) { return; }
    this.el.querySelector("[data-cards]").innerHTML = String(html`${this.data.dishes.map(dishCard)}`);
    this.el.querySelector("[data-feed]").innerHTML = String(feed(this.data.records));
    this.el.querySelector("[data-ticker]").innerHTML = String(ticker(this.data.alerts));
  }

  async onCard(e) {
    const card = e.target.closest("[data-item]"), btn = e.target.closest("button");
    if (!card || !btn) return;
    const dish = this.data.dishes.find((d) => d.item_id === card.dataset.item);
    if (btn.hasAttribute("data-time")) { this.timers.label = () => dish.name; return this.timers.add(dish.name, 20); }
    const qty = btn.hasAttribute("data-batch") ? dish.batch_output : await numpad({ title: dish.name, unit: dish.unit });
    if (!qty) return;
    const r = btn.getBoundingClientRect();
    if (await run(() => this.feed.produce(dish.item_id, qty), `${fmt(qty)} ${dish.unit} ${dish.name} recorded`)) {
      burst(r.left + r.width / 2, r.top + r.height / 2);
      this.refresh();
    }
  }

  clock() {
    const t = this.el.querySelector("[data-clock]");
    if (t) t.textContent = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  }

  /** Keep the tablet's screen on while the terminal is open (where the browser allows it). */
  async awake() {
    try { this.lock = await navigator.wakeLock?.request("screen"); } catch (e) { /* not allowed: fine */ }
  }
}

export async function terminal(el, q) {
  const b = await biz();
  const kitchens = b.locations.filter((l) => l.kind === "kitchen");
  const places = kitchens.length ? kitchens : b.locations;
  if (!places.length) { el.innerHTML = '<div class="card"><p>Add a kitchen location in Setup first.</p></div>'; return; }
  const chosen = places.find((l) => l.id === q.location) || places[0];
  await new Terminal(el, places, chosen.id).start();
}
