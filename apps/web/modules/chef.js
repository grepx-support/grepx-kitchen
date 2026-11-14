/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// Chef: recipe book, recipe cards, today's prep list by station, allergen chart (chef/*).
import { allergenPage } from "./chef/allergens.js";
import { bookPage } from "./chef/book.js";
import { cardPage } from "./chef/card.js";
import { prepPage } from "./chef/prep.js";

const base = { area: "chef", auth: "staff", tenant: true, perm: ["kitchen", "manage_business"] };
export const routes = [
  { ...base, path: "/chef", feature: "chef", nav: "Chef", key: "r", icon: "book", group: "Daily", render: bookPage, keywords: "recipe book cards method chef dishes menu" },
  { ...base, path: "/chef/recipe", feature: "chef", render: cardPage, keywords: "recipe card" },
  { ...base, path: "/chef/prep", feature: "chef", render: prepPage, keywords: "prep list station mise en place today" },
  { ...base, path: "/chef/allergens", feature: "chef", render: allergenPage, keywords: "allergen chart matrix gluten nuts milk veg" },
];
