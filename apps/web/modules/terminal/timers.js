/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// Kitchen timers: start one in a tap, see the ring run down, hear and feel it finish. Survive a page reload.
import { html, icon } from "/assets/kit/index.js";

/** One running timer: pure data + the maths of how much is left. */
export class Timer {
  constructor({ id, label, seconds, started = Date.now() }) { Object.assign(this, { id, label, seconds, started }); }
  get left() { return Math.max(0, this.seconds - (Date.now() - this.started) / 1000); }
  get done() { return this.left <= 0; }
  get fraction() { return this.left / this.seconds; }
}

export const clock = (s) => `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, "0")}`;

/** A short three-note chime; no sound files needed. */
function chime() {
  try {
    const audio = new AudioContext();
    [880, 1175, 1568].forEach((f, n) => {
      const o = audio.createOscillator(), g = audio.createGain();
      o.frequency.value = f; o.connect(g); g.connect(audio.destination);
      g.gain.setValueAtTime(0.0001, audio.currentTime + n * 0.18);
      g.gain.exponentialRampToValueAtTime(0.3, audio.currentTime + n * 0.18 + 0.02);
      g.gain.exponentialRampToValueAtTime(0.0001, audio.currentTime + n * 0.18 + 0.5);
      o.start(audio.currentTime + n * 0.18); o.stop(audio.currentTime + n * 0.18 + 0.55);
    });
  } catch (e) { /* no audio */ }
  navigator.vibrate?.([200, 100, 200, 100, 400]);
}

export class TimerBoard {
  static PRESETS = [3, 5, 10, 20, 45];

  /** store: kit LocalStore; slot: the element to draw into */
  constructor(store, slot) {
    Object.assign(this, { store, slot });
    this.timers = store.get("terminal.timers", []).map((t) => new Timer(t));
    this.rang = new Set(this.timers.filter((t) => t.done).map((t) => t.id));
    this.tick = setInterval(() => this.draw(), 500);
  }

  stop() { clearInterval(this.tick); }
  save() { this.store.set("terminal.timers", this.timers.map(({ id, label, seconds, started }) => ({ id, label, seconds, started }))); }

  add(label, minutes) {
    this.timers.push(new Timer({ id: `${Date.now()}`, label, seconds: minutes * 60 }));
    this.save();
    this.draw();
  }

  remove(id) { this.timers = this.timers.filter((t) => t.id !== id); this.rang.delete(id); this.save(); this.draw(); }

  draw() {
    this.timers.filter((t) => t.done && !this.rang.has(t.id)).forEach((t) => { this.rang.add(t.id); chime(); });
    const ring = (t) => { const c = 2 * Math.PI * 34; return html`<svg viewBox="0 0 80 80"><circle r="34" cx="40" cy="40" class="bg"/>
      <circle r="34" cx="40" cy="40" class="fg" stroke-dasharray="${c}" stroke-dashoffset="${c * (1 - t.fraction)}"/></svg>`; };
    this.slot.innerHTML = String(html`<div class="t-presets">${TimerBoard.PRESETS.map((m) => html`<button class="t-chip" data-min="${m}">${icon("clock", { size: 16 })} ${m} min</button>`)}</div>
      <div class="t-timers">${this.timers.length ? this.timers.map((t) => html`<div class="t-timer ${t.done ? "done" : ""}">${ring(t)}
        <b>${t.done ? "Done!" : clock(t.left)}</b><span>${t.label}</span><button class="t-x" data-off="${t.id}" aria-label="Remove timer">${icon("x", { size: 16 })}</button></div>`)
        : html`<p class="t-muted">No timers running - tap a time above.</p>`}</div>`);
    this.slot.querySelectorAll("[data-min]").forEach((b) => b.onclick = () => this.add(this.label?.() || "Timer", Number(b.dataset.min)));
    this.slot.querySelectorAll("[data-off]").forEach((b) => b.onclick = () => this.remove(b.dataset.off));
  }
}
