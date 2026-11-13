/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// A burst of colour from a point on the screen when a batch is recorded. Purely decorative; skipped for reduced motion.
const COLOURS = ["#f97316", "#facc15", "#22c55e", "#06b6d4", "#a855f7", "#ec4899"];

export function burst(x, y, count = 28) {
  if (matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  for (let n = 0; n < count; n++) {
    const bit = document.createElement("i");
    bit.className = "t-bit";
    const angle = (n / count) * Math.PI * 2, dist = 70 + Math.random() * 90;
    bit.style.cssText = `left:${x}px;top:${y}px;background:${COLOURS[n % COLOURS.length]};--dx:${Math.cos(angle) * dist}px;--dy:${Math.sin(angle) * dist}px;--r:${Math.random() * 720}deg`;
    document.body.append(bit);
    setTimeout(() => bit.remove(), 900);
  }
}
