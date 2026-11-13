/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// Kitchen: the target on the phone (KIT-03..05), record a production run and the ingredients used (KIT-06..09).
import { kitchen } from "./kitchen/page.js";

export const routes = [
  { path: "/kitchen", nav: "Kitchen", key: "k", icon: "pot", area: "kitchen", group: "Daily", auth: "staff", tenant: true, perm: "kitchen", render: kitchen },
];
