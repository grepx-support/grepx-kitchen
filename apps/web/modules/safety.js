/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// Food safety: today's checks at a place (safety/today), the log for inspectors (safety/log).
import { logPage } from "./safety/log.js";
import { safetyPage } from "./safety/today.js";

export const routes = [
  { path: "/safety", feature: "food_safety", nav: "Food safety", key: "f", icon: "shield", area: "safety", group: "Daily", auth: "staff", tenant: true,
    perm: ["kitchen", "closing", "manage_people", "manage_business"], render: safetyPage, keywords: "food safety haccp temperature fridge freezer cleaning checklist" },
  { path: "/safety/log", feature: "food_safety", area: "safety", auth: "staff", tenant: true, perm: ["manage_people", "manage_business"], render: logPage,
    keywords: "food safety log inspector haccp records" },
];
