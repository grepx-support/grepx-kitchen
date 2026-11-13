/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// Outbox: what the app sent for this business (outbox/sent.js) and what goes out on which channel (outbox/settings.js).
import { sent } from "./outbox/sent.js";
import { settings } from "./outbox/settings.js";

export const routes = [
  { path: "/outbox", nav: "Outbox", key: "x", icon: "mail", area: "outbox", group: "Setup", auth: "staff", tenant: true, perm: "manage_business", render: sent,
    keywords: "messages email whatsapp sms sent failed retry" },
  { path: "/outbox/settings", area: "outbox", auth: "staff", tenant: true, perm: "manage_business", render: settings,
    keywords: "notification settings channels message wording alerts reminders" },
];
