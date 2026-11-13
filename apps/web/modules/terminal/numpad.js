/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// A big on-screen number pad for wet or gloved hands: resolves with the number, or null.
import { html, icon } from "/assets/kit/index.js";

export function numpad({ title, unit, start = "" }) {
  return new Promise((resolve) => {
    let value = String(start);
    const el = document.createElement("div");
    el.className = "t-pad";
    const draw = () => {
      el.innerHTML = String(html`<div class="t-padbox"><h3>${title}</h3><output>${value || "0"}<small>${unit}</small></output>
        <div class="t-keys">${["1", "2", "3", "4", "5", "6", "7", "8", "9", ".", "0", "del"].map((k) =>
          html`<button data-k="${k}">${k === "del" ? icon("x", { size: 22 }) : k}</button>`)}</div>
        <div class="t-padgo"><button data-k="cancel">Cancel</button><button data-k="ok" class="go">Record</button></div></div>`);
    };
    el.onclick = (e) => {
      const k = e.target.closest("[data-k]")?.dataset.k;
      if (!k) { if (e.target === el) close(null); return; }
      if (k === "cancel") return close(null);
      if (k === "ok") return close(Number(value) > 0 ? Number(value) : null);
      value = k === "del" ? value.slice(0, -1) : (k === "." && value.includes(".")) || value.length > 6 ? value : value + k;
      draw();
    };
    const close = (v) => { el.remove(); resolve(v); };
    draw();
    document.body.append(el);
  });
}
