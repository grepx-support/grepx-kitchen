/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// Warehouse floor: lots and expiry (first expiry first out), bins, pick lists and picking, and the 3D view.
import { bins } from "./warehouse/bins.js";
import { lots } from "./warehouse/lots.js";
import { pickScreen } from "./warehouse/pick.js";
import { picks } from "./warehouse/picks.js";
import { view3d } from "./warehouse/view3d.js";
import { biz } from "./lib/business.js";
import { isHolding, remembered } from "./lib/place.js";

const FLOOR = { auth: "staff", tenant: true, area: "floor", group: "Warehouse" };

const withPlace = (page) => async (el, q) => {
  const b = await biz();
  const place = q.location || remembered(b.locations, isHolding);
  await page(el, q, b, place);
  el.querySelector("[data-pick]")?.addEventListener("change", (e) => { location.hash = `#${location.hash.slice(1).split("?")[0]}?location=${e.target.value}`; });
};

export const routes = [
  { path: "/warehouse", nav: "Warehouse floor", key: "w", icon: "layout", perm: "warehouse_in", ...FLOOR, render: withPlace(lots) },
  { path: "/warehouse/bins", perm: "warehouse_in", ...FLOOR, render: withPlace(bins) },
  { path: "/warehouse/picks", perm: "warehouse_out", ...FLOOR, render: withPlace(picks) },
  { path: "/warehouse/3d", perm: "warehouse_in", ...FLOOR, render: withPlace(view3d) },
  { path: "/warehouse/pick/:id", perm: "warehouse_out", ...FLOOR, render: (el, { args }) => pickScreen(el, args[0]) },
];
