/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// The kitchen terminal (wall tablet): full screen, big buttons, timers. See terminal/screen.js.
import { terminal } from "./terminal/screen.js";

export const routes = [
  { path: "/terminal", bare: true, auth: "staff", tenant: true, perm: "kitchen", render: terminal },
];
