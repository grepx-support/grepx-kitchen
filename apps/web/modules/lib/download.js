/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// Download a file the API makes (an Excel or CSV export, a template) with the signed-in session.
import { state, toast } from "/assets/app.js";

export async function download(path, fallbackName) {
  try {
    const res = await fetch(`/api/v1${path}`, { headers: { Authorization: `Bearer ${state.session?.token}` } });
    if (!res.ok) throw new Error("Could not make the file");
    const name = /filename="([^"]+)"/.exec(res.headers.get("Content-Disposition") || "")?.[1] || fallbackName;
    const a = Object.assign(document.createElement("a"), { href: URL.createObjectURL(await res.blob()), download: name });
    a.click();
    setTimeout(() => URL.revokeObjectURL(a.href), 60000);
  } catch (e) { toast(e.message); }
}
