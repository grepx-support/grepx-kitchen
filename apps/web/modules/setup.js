/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// Business setup by its owner (BUS-02/03/06, ACC-01..03, KIT-01/02, ORD-01, COS-01/02/07, R4, R9, R10).
import { api, esc, run } from "../../app.js";
import { biz, fmt, resetBiz } from "./lib.js";

const MODULES = { kitchen: "Kitchen", inventory: "Inventory", orders: "Reorder and purchase orders", costing: "Costing and sales", closing: "Staff closing" };
const KINDS = ["warehouse", "kitchen", "store", "truck"];
const opt = (list, v) => list.map((x) => `<option ${x === v ? "selected" : ""}>${esc(x)}</option>`).join("");

export const routes = [
  { path: "/setup", nav: "Setup", auth: "staff", perm: "manage_business", render: async function draw(el, q) {
    const s = await api("/setup");
    const tab = q.tab || "business";
    const b = s.business, st = b.settings || {};
    const items = Object.fromEntries(s.items.map((i) => [i.id, i]));
    const sup = Object.fromEntries(s.suppliers.map((x) => [x.id, x]));
    const tabs = { business: "Business", locations: "Locations", items: "Items", suppliers: "Suppliers", recipes: "Recipes", users: "Users", roles: "Roles", costs: "Monthly costs" };
    const body = {
      business: () => `<form id="biz" class="card"><div class="row"><div><label>Name</label><input name="name" value="${esc(b.name)}"></div><div><label>Currency</label><input name="currency" value="${esc(b.currency)}" maxlength="3"></div>
          <div><label>Time zone</label><input name="timezone" value="${esc(b.timezone)}"></div></div>
        <h2 style="margin-top:14px">Modules</h2>${Object.entries(MODULES).map(([k, v]) => `<label><input type="checkbox" name="m_${k}" style="width:auto" ${b.modules?.[k] !== false ? "checked" : ""}> ${esc(v)}</label>`).join("")}
        <h2 style="margin-top:14px">Planning and costing</h2><div class="row">
          <div><label>Past weeks for targets (1-3)</label><input name="target_weeks" type="number" min="1" max="3" value="${esc(st.target_weeks)}"></div>
          <div><label>Safety buffer %</label><input name="safety_pct" type="number" min="0" value="${esc(st.safety_pct)}"></div>
          <div><label>Large change in a recommendation %</label><input name="large_change_pct" type="number" min="1" value="${esc(st.large_change_pct)}"></div>
          <div><label>COGS range from %</label><input name="cogs_min" type="number" min="0" max="100" value="${esc(st.cogs_min)}"></div>
          <div><label>to %</label><input name="cogs_max" type="number" min="0" max="100" value="${esc(st.cogs_max)}"></div></div>
        <label>Sales types at closing (comma separated)</label><input name="sales_types" value="${esc((st.sales_types || []).join(", "))}">
        <p><button class="btn primary">Save</button></p></form>`,
      locations: () => `<div class="card"><table><tr><th>Name</th><th>Type</th><th>Holds stock</th><th>Days of cover</th><th>Count every</th><th></th></tr>
          ${s.locations.map((l) => `<tr><td>${esc(l.name)}${l.active === false ? ' <span class="muted">(closed)</span>' : ""}</td><td>${esc(l.kind)}</td><td>${l.holding ? "yes" : ""}</td><td>${esc(l.days_of_cover)}</td><td>${esc(l.count_every_days)} day(s)</td>
          <td><a href="#/setup?tab=locations&edit=${esc(l.id)}">Edit</a></td></tr>`).join("")}</table></div><br>${locForm(s.locations.find((l) => l.id === q.edit))}`,
      items: () => `<div class="card"><table><tr><th>Item</th><th>Type</th><th>Unit</th><th>Cost</th><th>Supplier</th><th></th></tr>
          ${s.items.map((i) => `<tr><td>${esc(i.name)}${i.active === false ? ' <span class="muted">(archived)</span>' : ""}</td><td>${esc(i.kind)}</td><td>${esc(i.unit)}</td><td>${fmt(i.cost)}</td><td>${esc(sup[i.supplier_id]?.name || "")}</td>
          <td><a href="#/setup?tab=items&edit=${esc(i.id)}">Edit</a></td></tr>`).join("")}</table></div><br>${itemForm(items[q.edit], s.suppliers)}`,
      suppliers: () => `<div class="card"><table><tr><th>Supplier</th><th>Phone / WhatsApp</th><th>Contact</th><th></th></tr>
          ${s.suppliers.map((x) => `<tr><td>${esc(x.name)}</td><td>${esc(x.phone)}</td><td>${esc(x.contact)}</td><td><a href="#/setup?tab=suppliers&edit=${esc(x.id)}">Edit</a></td></tr>`).join("")}</table></div><br>${supForm(sup[q.edit])}`,
      recipes: () => s.items.filter((i) => i.kind === "finished").map((p) => { const r = s.recipes.find((x) => x.id === p.id) || {};
        return `<form class="card rec" data-item="${esc(p.id)}"><h2>${esc(p.name)}</h2><div class="row"><div><label>One batch makes</label><input name="out" type="number" min="0" step="any" value="${esc(r.batch_output ?? "")}"></div><div class="muted">${esc(p.unit)}</div></div>
          <label>Ingredients for one batch (optional) - one per line: name = quantity</label><textarea name="ing" rows="3">${esc((r.ingredients || []).map((x) => `${items[x.item_id]?.name || x.item_id} = ${x.qty}`).join("\n"))}</textarea>
          <p><button class="btn">Save recipe</button></p></form><br>`; }).join("") || '<div class="card"><p class="muted">Add finished products under Items first.</p></div>',
      users: () => `<div class="card"><table><tr><th>Name</th><th>Email</th><th>Role</th></tr>${s.users.map((u) => `<tr><td>${esc(u.name)}</td><td>${esc(u.email)}</td>
          <td><select data-user="${esc(u.id)}"><option value="">-</option>${s.roles.map((r) => `<option value="${esc(r.id)}" ${r.id === u.staff_role_id ? "selected" : ""}>${esc(r.name)}</option>`).join("")}</select></td></tr>`).join("")}</table></div><br>
        <form id="nu" class="card"><h2>Add a user</h2><div class="row"><div><label>Name</label><input name="name" required></div><div><label>Email (login)</label><input name="email" type="email" required></div>
          <div><label>Phone</label><input name="phone" required placeholder="+61 412 345 678"></div><div><label>Password (8+)</label><input name="password" type="password" minlength="8" required></div>
          <div><label>Role</label><select name="role">${s.roles.map((r) => `<option value="${esc(r.id)}">${esc(r.name)}</option>`).join("")}</select></div></div><p><button class="btn primary">Add user</button></p></form>`,
      roles: () => s.roles.map((r) => `<form class="card role" data-role="${esc(r.id)}"><h2>${esc(r.name)}</h2>${s.permissions.map((p) => `<label><input type="checkbox" style="width:auto" value="${esc(p.id)}" ${(r.perms || []).includes(p.id) ? "checked" : ""}> ${esc(p.label || p.id)}</label>`).join("")}
          <p><button class="btn">Save</button></p></form><br>`).join(""),
      costs: () => `<form id="oh" class="card"><p class="muted">Monthly amounts per location; they are spread equally over the days of the month.</p><div class="row">
          <div><label>Location</label><select name="loc">${s.locations.map((l) => `<option value="${esc(l.id)}">${esc(l.name)}</option>`).join("")}</select></div><div><label>Month</label><input name="month" type="month" value="${new Date().toISOString().slice(0, 7)}"></div>
          <div><label>Labour</label><input name="labour" type="number" min="0" step="0.01" required></div><div><label>Rent</label><input name="rent" type="number" min="0" step="0.01" required></div><div><label>Other</label><input name="other" type="number" min="0" step="0.01" required></div></div>
          <p><button class="btn primary">Save</button></p></form><br><div class="card"><table><tr><th>Location</th><th>Month</th><th>Labour</th><th>Rent</th><th>Other</th></tr>
          ${s.overheads.map((o) => `<tr><td>${esc(s.locations.find((l) => l.id === o.location_id)?.name || "")}</td><td>${esc(o.month)}</td><td>${fmt(o.labour)}</td><td>${fmt(o.rent)}</td><td>${fmt(o.other)}</td></tr>`).join("")}</table></div>`,
    };
    el.innerHTML = `<h1>Setup</h1><nav class="tabs">${Object.entries(tabs).map(([k, v]) => `<a class="btn small ${k === tab ? "primary" : ""}" href="#/setup?tab=${k}">${v}</a>`).join(" ")}</nav><br>${body[tab]()}`;
    const redraw = () => draw(el, { tab });
    const post = (path, payload, done) => run(() => api(path, { method: "POST", body: payload }), done);
    const f = (sel) => el.querySelector(sel);
    if (f("#biz")) f("#biz").onsubmit = async (e) => { e.preventDefault(); const d = new FormData(e.target);
      const body = { name: d.get("name"), currency: d.get("currency"), timezone: d.get("timezone"), modules: Object.fromEntries(Object.keys(MODULES).map((k) => [k, !!d.get(`m_${k}`)])),
        settings: { target_weeks: d.get("target_weeks"), safety_pct: d.get("safety_pct"), large_change_pct: d.get("large_change_pct"), cogs_min: d.get("cogs_min"), cogs_max: d.get("cogs_max"),
          sales_types: d.get("sales_types").split(",").map((x) => x.trim()).filter(Boolean) } };
      if (await run(() => api("/setup/business", { method: "PATCH", body }), "Saved")) { resetBiz(); redraw(); } };
    if (f("#loc")) f("#loc").onsubmit = async (e) => { e.preventDefault(); const d = new FormData(e.target);
      if (await post("/setup/locations", { location_id: d.get("id") || undefined, name: d.get("name"), kind: d.get("kind"), holding: !!d.get("holding"), address: d.get("address"),
        days_of_cover: Number(d.get("cover")), count_every_days: Number(d.get("every")), active: !d.get("closed") }, "Location saved")) { resetBiz(); location.hash = "#/setup?tab=locations"; } };
    if (f("#item")) f("#item").onsubmit = async (e) => { e.preventDefault(); const d = new FormData(e.target);
      if (await post("/setup/items", { item_id: d.get("id") || undefined, name: d.get("name"), kind: d.get("kind"), unit: d.get("unit"), cost: Number(d.get("cost") || 0),
        supplier_id: d.get("supplier"), category: d.get("category"), active: !d.get("archived") }, "Item saved")) location.hash = "#/setup?tab=items"; };
    if (f("#sup")) f("#sup").onsubmit = async (e) => { e.preventDefault(); const d = new FormData(e.target);
      if (await post("/setup/suppliers", { supplier_id: d.get("id") || undefined, name: d.get("name"), phone: d.get("phone"), email: d.get("email"), contact: d.get("contact"), notes: d.get("notes") }, "Supplier saved")) location.hash = "#/setup?tab=suppliers"; };
    el.querySelectorAll("form.rec").forEach((r) => r.onsubmit = async (e) => { e.preventDefault(); const d = new FormData(r);
      const byName = Object.fromEntries(s.items.map((i) => [i.name.toLowerCase(), i.id]));
      const ingredients = d.get("ing").split("\n").map((x) => x.split("=")).filter((p) => p.length === 2 && p[0].trim()).map(([n, q]) => ({ item_id: byName[n.trim().toLowerCase()] || n.trim(), qty: Number(q) }));
      if (await post("/setup/recipes", { item_id: r.dataset.item, batch_output: Number(d.get("out")), ingredients }, "Recipe saved")) redraw(); });
    el.querySelectorAll("[data-user]").forEach((sel) => sel.onchange = () => post(`/setup/users/${sel.dataset.user}/role`, { staff_role: sel.value }, "Role changed"));
    if (f("#nu")) f("#nu").onsubmit = async (e) => { e.preventDefault(); const d = new FormData(e.target);
      if (await post("/setup/users", { name: d.get("name"), email: d.get("email"), phone: d.get("phone"), password: d.get("password"), staff_role: d.get("role") }, "User added")) redraw(); };
    el.querySelectorAll("form.role").forEach((r) => r.onsubmit = async (e) => { e.preventDefault();
      const perms = [...r.querySelectorAll("input:checked")].map((i) => i.value);
      if (await post(`/setup/roles/${encodeURIComponent(r.dataset.role)}`, { perms }, "Role saved")) redraw(); });
    if (f("#oh")) f("#oh").onsubmit = async (e) => { e.preventDefault(); const d = new FormData(e.target);
      if (await post("/setup/overheads", { location_id: d.get("loc"), month: d.get("month"), labour: d.get("labour"), rent: d.get("rent"), other: d.get("other") }, "Saved")) redraw(); };
  } },
];

function locForm(l = {}) {
  return `<form id="loc" class="card"><h2>${l.id ? "Edit location" : "Add a location"}</h2><input type="hidden" name="id" value="${esc(l.id || "")}"><div class="row">
    <div><label>Name</label><input name="name" required value="${esc(l.name || "")}"></div><div><label>Type</label><select name="kind">${opt(KINDS, l.kind || "store")}</select></div>
    <div><label>Days of cover</label><input name="cover" type="number" min="1" max="60" value="${esc(l.days_of_cover ?? 3)}"></div>
    <div><label>Count every</label><select name="every">${[1, 3, 7].map((n) => `<option value="${n}" ${n === (l.count_every_days || 1) ? "selected" : ""}>${n} day(s)</option>`).join("")}</select></div></div>
    <label>Address (for the live map)</label><input name="address" value="${esc(l.address || "")}">
    <label><input type="checkbox" name="holding" style="width:auto" ${l.holding ? "checked" : ""}> Holds stock for the other locations (warehouse or kitchen storage area)</label>
    ${l.id ? `<label><input type="checkbox" name="closed" style="width:auto" ${l.active === false ? "checked" : ""}> Closed</label>` : ""}<p><button class="btn primary">Save</button></p></form>`;
}
function itemForm(i = {}, suppliers = []) {
  return `<form id="item" class="card"><h2>${i.id ? "Edit item" : "Add an item"}</h2><input type="hidden" name="id" value="${esc(i.id || "")}"><div class="row">
    <div><label>Name</label><input name="name" required value="${esc(i.name || "")}"></div><div><label>Type</label><select name="kind">${opt(["ingredient", "finished", "supply"], i.kind || "ingredient")}</select></div>
    <div><label>Unit</label><input name="unit" required placeholder="kg, box, each" value="${esc(i.unit || "")}"></div><div><label>Cost per unit</label><input name="cost" type="number" min="0" step="0.0001" value="${esc(i.cost ?? "")}"></div>
    <div><label>Supplier</label><select name="supplier"><option value="">-</option>${suppliers.map((s) => `<option value="${esc(s.id)}" ${s.id === i.supplier_id ? "selected" : ""}>${esc(s.name)}</option>`).join("")}</select></div>
    <div><label>Category</label><input name="category" value="${esc(i.category || "")}"></div></div>
    ${i.id ? `<label><input type="checkbox" name="archived" style="width:auto" ${i.active === false ? "checked" : ""}> Archived</label>` : ""}<p><button class="btn primary">Save</button></p></form>`;
}
function supForm(x = {}) {
  return `<form id="sup" class="card"><h2>${x.id ? "Edit supplier" : "Add a supplier"}</h2><input type="hidden" name="id" value="${esc(x.id || "")}"><div class="row">
    <div><label>Name</label><input name="name" required value="${esc(x.name || "")}"></div><div><label>Phone / WhatsApp</label><input name="phone" value="${esc(x.phone || "")}"></div>
    <div><label>Email</label><input name="email" type="email" value="${esc(x.email || "")}"></div><div><label>Contact person</label><input name="contact" value="${esc(x.contact || "")}"></div></div>
    <label>Notes</label><textarea name="notes" rows="2">${esc(x.notes || "")}</textarea><p><button class="btn primary">Save</button></p></form>`;
}
