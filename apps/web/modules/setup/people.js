/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// Users (add one, change their role) and roles (what each role may do) - ACC-01..03.
import { avatar, html } from "/assets/kit/index.js";
import { post, values } from "./common.js";

export const users = {
  id: "users", label: "Users", icon: "users",
  render(el, s, q, { redraw }) {
    el.innerHTML = String(html`<section class="card"><ul class="k-sort">${s.users.map((u) => html`<li><span></span>${avatar(u.name)}<span class="who"><b>${u.name}</b><small>${u.email}</small></span>
        <select data-user="${u.id}" aria-label="Role of ${u.name}"><option value="">-</option>${s.roles.map((r) => html`<option value="${r.id}" ${r.id === u.staff_role_id ? "selected" : ""}>${r.name}</option>`)}</select></li>`)}</ul></section>
      <form class="card accent k-section"><h2>Add a user</h2><div class="row"><label>Name<input name="name" required></label><label>Email (login)<input name="email" type="email" required></label>
        <label>Phone<input name="phone" required placeholder="+61 412 345 678"></label><label>Password (8+)<input name="password" type="password" minlength="8" required></label>
        <label>Role<select name="role">${s.roles.map((r) => html`<option value="${r.id}">${r.name}</option>`)}</select></label></div><p><button class="btn primary">Add user</button></p></form>`);
    el.querySelectorAll("[data-user]").forEach((sel) => sel.onchange = () => post(`/setup/users/${sel.dataset.user}/role`, { staff_role: sel.value }, "Role changed"));
    el.querySelector("form").onsubmit = async (e) => {
      e.preventDefault();
      const v = values(e.target);
      if (await post("/setup/users", { name: v.name, email: v.email, phone: v.phone, password: v.password, staff_role: v.role }, "User added")) redraw();
    };
  },
};

export const roles = {
  id: "roles", label: "Roles", icon: "shield",
  render(el, s, q, { redraw }) {
    el.innerHTML = String(html`<div class="grid two">${s.roles.map((r) => html`<form class="card accent" data-role="${r.id}"><h2>${r.name}</h2>
      <div class="k-perms">${s.permissions.map((p) => html`<label class="check"><input type="checkbox" value="${p.id}" ${(r.perms || []).includes(p.id) ? "checked" : ""}> ${p.label || p.id}</label>`)}</div>
      <p><button class="btn">Save</button></p></form>`)}</div>`);
    el.querySelectorAll("form[data-role]").forEach((f) => f.onsubmit = async (e) => {
      e.preventDefault();
      const perms = [...f.querySelectorAll("input:checked")].map((i) => i.value);
      if (await post(`/setup/roles/${encodeURIComponent(f.dataset.role)}`, { perms }, "Role saved")) redraw();
    });
  },
};
