/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// The closing wizard: one draft moving through the steps; Back / Next keep what was typed; Submit sends it once.
import { api, run } from "/assets/app.js";
import { Component, html, icon, steps } from "/assets/kit/index.js";
import * as view from "./steps.js";

const VIEWS = [view.count, view.sales, view.issues, view.check];

export class ClosingWizard extends Component {
  /** props: { form (from /closing/form), location, onDone } */
  constructor(props) {
    super(props);
    this.step = 0;
    this.draft = { counts: {}, sales: {}, issues: "", staff: props.form.staff_name || "", date: props.form.date };
  }

  render() {
    const last = this.step === VIEWS.length - 1;
    return html`<div>${steps(view.STEPS, this.step)}<section class="card accent">${VIEWS[this.step](this.props.form, this.draft)}
      <div class="k-nav"><button type="button" class="btn" data-back ${this.step ? "" : "disabled"}>Back</button>
        ${last ? html`<button type="button" class="btn primary" data-submit>${icon("check", { size: 16 })} Submit closing</button>`
          : html`<button type="button" class="btn primary" data-next>Next ${icon("arrow", { size: 16 })}</button>`}</div></section></div>`;
  }

  mounted() {
    const d = this.draft;
    this.el.querySelectorAll("[data-count]").forEach((i) => i.oninput = () => {
      if (i.value === "") delete d.counts[i.dataset.count]; else d.counts[i.dataset.count] = Number(i.value);
      i.closest("label").classList.toggle("done", i.value !== "");
    });
    this.el.querySelectorAll("[data-sale]").forEach((i) => i.oninput = () => { if (i.value === "") delete d.sales[i.dataset.sale]; else d.sales[i.dataset.sale] = Number(i.value); });
    const bind = (sel, key) => { const i = this.el.querySelector(sel); if (i) i.oninput = () => { d[key] = i.value; }; };
    bind("[data-issues]", "issues"); bind("[data-staff]", "staff"); bind("[data-date]", "date");
    this.el.querySelector("[data-back]").onclick = () => this.go(-1);
    this.el.querySelector("[data-next]")?.addEventListener("click", () => this.go(1));
    this.el.querySelector("[data-submit]")?.addEventListener("click", () => this.submit());
  }

  go(by) { this.step = Math.max(0, Math.min(VIEWS.length - 1, this.step + by)); this.update(); scrollTo({ top: 0, behavior: "smooth" }); }

  async submit() {
    const d = this.draft;
    const body = { location_id: this.props.location, date: d.date, staff_name: d.staff, issues: d.issues, sales: d.sales,
      counts: Object.entries(d.counts).map(([item_id, qty]) => ({ item_id, qty })) };
    if (await run(() => api("/closing", { method: "POST", body }), "Closing submitted - thank you")) this.props.onDone();
  }
}
