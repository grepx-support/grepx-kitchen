/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// The public product page (no login, no app frame): what it does, how it works, plans, and "request a demo".
import { api, state, toast } from "/assets/app.js";
import { html, icon } from "/assets/kit/index.js";

const FEATURES = [
  ["pot", "#f97316", "Kitchen production", "Plan what to cook from sales and par, issue ingredients by recipe, record what came out and what was wasted."],
  ["box", "#0ea5e9", "Stock in every location", "Central store, kitchens and outlets: receive, send, transfer and count, with every movement kept."],
  ["layout", "#8b5cf6", "Warehouse floor", "Bins, lots with expiry, first-expiry-first-out picking and pick lists that become transfers on their own."],
  ["truck", "#0891b2", "Delivery runs", "Group deliveries into runs, order the stops, give drivers an arrival time and take a signature as proof."],
  ["alert", "#e11d48", "Inventory control", "Minimum and maximum levels, blind stock takes, ABC analysis, days of cover - and an alert before anything runs out or expires."],
  ["cart", "#7c3aed", "Purchasing", "Suggested orders from usage and par; send the purchase order to the supplier by email, WhatsApp or SMS."],
  ["chart", "#16a34a", "Daily cost", "Food cost by outlet and by day, waste included, valued at what you actually paid for each lot."],
  ["clipboard", "#2563eb", "Day closing", "Each outlet closes its day in a few minutes; the numbers are locked and the gaps are visible."],
];

const STEPS = [
  ["Set up in an afternoon", "Your locations, items, suppliers and recipes - or import them from a sheet."],
  ["Run the day on a phone", "Staff record what comes in, goes out and gets cooked, with the barcode scanner if you like."],
  ["See cost and stock live", "Owners get the alerts and the daily cost; nothing waits for month end."],
];

const PLANS = [
  ["Single kitchen", "For one kitchen with its store.", ["Stock, kitchen and closing", "Recipes and daily cost", "Up to 10 staff"]],
  ["Central kitchen", "For a central kitchen supplying outlets.", ["Everything in Single kitchen", "Warehouse lots, bins and picking", "Delivery runs with proof of delivery", "Inventory control and alerts"], true],
  ["Group", "For several brands or regions.", ["Everything in Central kitchen", "Purchasing by email, WhatsApp and SMS", "Support access and onboarding", "Unlimited staff"]],
];

const FAQ = [
  ["Does it work on a phone?", "Yes. Every screen works on a phone; drivers and store staff use it in the browser, nothing to install."],
  ["Can we bring our existing items and recipes?", "Yes. We load them from your sheet during onboarding."],
  ["How are messages sent?", "Through your own email, WhatsApp and SMS accounts once they are connected. Until then everything is kept in the outbox so you can see exactly what would go out."],
  ["Is our data kept apart from other businesses?", "Yes. Every record belongs to one business, and every screen and report only reads that business's records."],
];

export async function landing(el) {
  const p = state.product || {};
  el.innerHTML = String(html`<div class="lp">
    <header class="lp-top"><a class="lp-brand" href="#/welcome"><span>${p.logo || ""}</span>${p.name || "Kitchen"}</a>
      <nav><a href="#features" data-jump>Features</a><a href="#how" data-jump>How it works</a><a href="#plans" data-jump>Plans</a>
      <a class="btn small" href="#/login">Sign in</a><a class="btn small primary" href="#demo" data-jump>Request a demo</a></nav></header>

    <section class="lp-hero"><div>
      <p class="lp-kicker">${icon("sparkle", { size: 15 })} For central kitchens, cloud kitchens and restaurant groups</p>
      <h1>Know what every plate costs - <em>today</em>, not at month end.</h1>
      <p class="lp-lead">${p.name || "Kitchen"} runs your store, kitchen, warehouse and deliveries in one place, and turns every movement into stock, cost and alerts as it happens.</p>
      <div class="lp-cta"><a class="btn primary" href="#demo" data-jump>Request a demo ${icon("arrow", { size: 16 })}</a><a class="btn" href="#features" data-jump>See what it does</a></div></div>
      <div class="lp-mock" aria-hidden="true"><div class="lp-mbar"><i></i><i></i><i></i></div>
        <div class="lp-mkpi"><b>28.4%</b><span>food cost today</span></div><div class="lp-mkpi"><b>3</b><span>alerts</span></div>
        <div class="lp-mrow" style="--w:82%;--c:#0ea5e9"><span>Chicken thigh</span><i></i></div>
        <div class="lp-mrow" style="--w:46%;--c:#f59e0b"><span>Cream - expires in 2 days</span><i></i></div>
        <div class="lp-mrow" style="--w:18%;--c:#e11d48"><span>Basmati rice - below minimum</span><i></i></div>
        <div class="lp-mrun">${icon("truck", { size: 16 })} Run 4 · 6 stops · back 14:20</div></div></section>

    <section class="lp-sec" id="features"><h2>Everything between the supplier and the plate</h2>
      <div class="lp-grid">${FEATURES.map(([ic, c, t, d]) => html`<article class="lp-feat" style="--c:${c}"><span>${icon(ic)}</span><h3>${t}</h3><p>${d}</p></article>`)}</div></section>

    <section class="lp-sec lp-band" id="how"><h2>How it works</h2>
      <ol class="lp-steps">${STEPS.map(([t, d], n) => html`<li><b>${n + 1}</b><h3>${t}</h3><p>${d}</p></li>`)}</ol></section>

    <section class="lp-sec" id="plans"><h2>Plans</h2><p class="lp-sub">Priced by number of locations. Tell us about your kitchen and we will send a quote.</p>
      <div class="lp-plans">${PLANS.map(([t, d, list, best]) => html`<article class="lp-plan ${best ? "best" : ""}">${best ? html`<span class="lp-tag">Most chosen</span>` : ""}
        <h3>${t}</h3><p>${d}</p><ul>${list.map((x) => html`<li>${icon("check", { size: 15 })} ${x}</li>`)}</ul>
        <a class="btn ${best ? "primary" : ""}" href="#demo" data-jump data-plan="${t}">Ask for a quote</a></article>`)}</div></section>

    <section class="lp-sec lp-band" id="demo"><div class="lp-demo"><div><h2>Request a demo</h2><p>We will show it on your own items and recipes - about 30 minutes.</p>
        <ul class="lp-list"><li>${icon("check", { size: 15 })} A walk-through for your team</li><li>${icon("check", { size: 15 })} A trial business set up for you</li><li>${icon("check", { size: 15 })} A quote for your locations</li></ul></div>
      <form class="card lp-form" novalidate>
        <label>Your name<input name="name" required autocomplete="name" maxlength="80"></label>
        <label>Work email<input name="email" type="email" required autocomplete="email" maxlength="120"></label>
        <label>Phone or WhatsApp<input name="phone" type="tel" autocomplete="tel" maxlength="30"></label>
        <label>Business<input name="company" autocomplete="organization" maxlength="120"></label>
        <label>Locations<select name="size"><option>1</option><option>2-5</option><option>6-20</option><option>More than 20</option></select></label>
        <label class="lp-wide">Anything we should know?<textarea name="message" rows="3" maxlength="1000"></textarea></label>
        <label class="lp-hp" aria-hidden="true">Website<input name="website" tabindex="-1" autocomplete="off"></label>
        <button class="btn primary lp-wide">Send request</button><p class="lp-done lp-wide" hidden>${icon("check")} Thank you - we will be in touch within one working day.</p></form></div></section>

    <section class="lp-sec" id="faq"><h2>Questions</h2>${FAQ.map(([q, a]) => html`<details class="lp-faq"><summary>${q}</summary><p>${a}</p></details>`)}</section>
    <footer class="lp-foot"><span>© ${new Date().getFullYear()} GrepX</span><a href="#/login">Sign in</a></footer></div>`);

  // In-page links: scroll, keep the hash route as it is.
  el.querySelectorAll("[data-jump]").forEach((a) => a.onclick = (e) => {
    e.preventDefault();
    el.querySelector(a.getAttribute("href"))?.scrollIntoView({ behavior: "smooth" });
    if (a.dataset.plan) el.querySelector("[name=message]").value ||= `Interested in the ${a.dataset.plan} plan.`;
  });
  const form = el.querySelector(".lp-form");
  form.onsubmit = async (e) => {
    e.preventDefault();
    if (!form.reportValidity()) return;
    const btn = form.querySelector("button");
    btn.disabled = true;
    try {
      await api("/public/demo", { method: "POST", body: Object.fromEntries(new FormData(form)) });
      form.querySelectorAll("label").forEach((l) => l.hidden = true);
      btn.hidden = true;
      form.querySelector(".lp-done").hidden = false;
    } catch (err) {
      toast(err.message || "Could not send - please try again in a few minutes.");
      btn.disabled = false;
    }
  };
}

export const routes = [{ path: "/welcome", bare: true, render: landing }];
