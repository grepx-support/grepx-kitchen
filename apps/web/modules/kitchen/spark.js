/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// A small line chart as SVG markup: the last weeks (solid) running into the forecast (dashed), with a marker where
// today is. Pure - takes numbers, returns a string.
export function spark(history, forecast, { width = 280, height = 70, colour = "#7c3aed", ahead = "#f97316" } = {}) {
  const all = [...history, ...forecast];
  if (!all.length) return "";
  const top = Math.max(1, ...all.map((p) => p.qty)), step = width / Math.max(1, all.length - 1);
  const xy = (p, i) => `${(i * step).toFixed(1)},${(height - 6 - (p.qty / top) * (height - 14)).toFixed(1)}`;
  const past = history.map(xy).join(" ");
  const future = [history[history.length - 1], ...forecast].filter(Boolean).map((p, i) => xy(p, i + Math.max(0, history.length - 1))).join(" ");
  const split = Math.max(0, history.length - 1) * step;
  return `<svg viewBox="0 0 ${width} ${height}" class="fc-spark" preserveAspectRatio="none" role="img" aria-label="Sold in the last weeks and the forecast">
    <defs><linearGradient id="fcg" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="${colour}" stop-opacity=".28"/><stop offset="1" stop-color="${colour}" stop-opacity="0"/></linearGradient></defs>
    <rect x="${split}" y="0" width="${width - split}" height="${height}" fill="${ahead}" opacity=".07"/>
    ${history.length > 1 ? `<polygon points="0,${height} ${past} ${split},${height}" fill="url(#fcg)"/>` : ""}
    <polyline points="${past}" fill="none" stroke="${colour}" stroke-width="2" stroke-linejoin="round"/>
    <polyline points="${future}" fill="none" stroke="${ahead}" stroke-width="2.4" stroke-dasharray="5 4" stroke-linejoin="round"/>
    <line x1="${split}" x2="${split}" y1="0" y2="${height}" stroke="currentColor" opacity=".25" stroke-dasharray="2 3"/></svg>`;
}
