/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// Home: a personal dashboard of widgets for this user's role - drag, resize and hide them (saved on this device).
import { state, store } from "/assets/app.js";
import { DashboardGrid } from "/assets/kit/index.js";
import { widgets } from "./dashboard/registry.js";
import { biz } from "./lib/business.js";

export const routes = [
  { path: "/", nav: "Home", icon: "home", area: "home", auth: "user", tenant: true, render: async (el) => {
    const b = await biz(true);
    new DashboardGrid({ registry: widgets, store, key: `kitchen.dashboard.${state.me?.user_id || state.me?.id || ""}`, ctx: { b } }).mount(el);
  } },
];
