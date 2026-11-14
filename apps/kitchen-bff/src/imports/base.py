# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Bulk import and export (Template Method): a kind of record says its columns, how a row becomes the body its owning
service saves, how it is matched to a record already there (so importing again updates instead of duplicating), and
how its records are written out. The base reads the file, checks every row before anything is saved (preview), then
saves row by row, each through the same action and checks as the screen."""
from __future__ import annotations

from dataclasses import dataclass, field

from grepx_bff.errors import ApiError
from grepx_bff.tabular import norm


@dataclass(frozen=True)
class Column:
    heading: str
    key: str
    required: bool = False
    kind: str = "text"            # text / number / int / date / list (comma separated)
    example: str = ""
    help: str = ""


@dataclass
class Prepared:
    rows: list[int]
    label: str
    action: str = "create"        # create / update
    body: dict = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)


def typed(col: Column, raw: str):
    """A cell as its column's type; ValueError with a reader's message when it is not one."""
    raw = (raw or "").strip()
    if not raw:
        if col.required:
            raise ValueError(f"{col.heading} is needed")
        return None
    if col.kind in ("number", "int"):
        try:
            v = float(raw.replace(",", ""))
        except ValueError:
            raise ValueError(f"{col.heading} must be a number (got {raw!r})")
        if v < 0:
            raise ValueError(f"{col.heading} can't be below zero")
        return int(v) if col.kind == "int" or v.is_integer() else v
    if col.kind == "date":
        import datetime as dt
        try:
            return dt.date.fromisoformat(raw[:10]).isoformat()
        except ValueError:
            raise ValueError(f"{col.heading} must be a date like 2026-11-14")
    if col.kind == "list":
        return [p.strip() for p in raw.replace(";", ",").split(",") if p.strip()]
    return raw


class Importer:
    kind = ""
    title = ""
    columns: tuple[Column, ...] = ()
    notes: tuple[str, ...] = ()

    # --- what each kind says ---
    def context(self, k) -> dict:
        return {}

    def prepare(self, values: dict, ctx: dict) -> tuple[dict, str, str]:
        """(body, create | update, label) for one row's typed values; ValueError(message) when it can't be saved."""
        raise NotImplementedError

    def save(self, k, body: dict) -> None:
        raise NotImplementedError

    def export(self, k, ctx: dict) -> list[list]:
        raise NotImplementedError

    # --- the same for every kind ---
    def values(self, row: dict) -> tuple[dict, list[str]]:
        out, errors = {}, []
        for col in self.columns:
            try:
                out[col.key] = typed(col, row.get(norm(col.heading), ""))
            except ValueError as exc:
                errors.append(str(exc))
        return out, errors

    def plan(self, rows: list[dict], ctx: dict) -> list[Prepared]:
        missing = [c.heading for c in self.columns if c.required and not any(norm(c.heading) in r for r in rows)]
        if missing:
            raise ApiError("MISSING_COLUMNS", 400, f"The file has no {', '.join(missing)} column - download the template to see the headings.")
        out = []
        for row in rows:
            values, errors = self.values(row)
            p = Prepared([row["_row"]], str(values.get(self.columns[0].key) or ""), errors=errors)
            if not errors:
                try:
                    p.body, p.action, p.label = self.prepare(values, ctx)
                except ValueError as exc:
                    p.errors.append(str(exc))
            out.append(p)
        return out

    def run(self, k, plan: list[Prepared]) -> list[Prepared]:
        for p in plan:
            if p.errors:
                continue
            try:
                self.save(k, p.body)
            except ApiError as exc:
                p.errors.append((exc.detail or {}).get("message") or str(exc.detail))
        return plan

    def template(self) -> list[list]:
        return [[c.example for c in self.columns]]

    def headings(self) -> list[str]:
        return [c.heading + (" *" if c.required else "") for c in self.columns]

    def help(self) -> list[str]:
        return [*self.notes, "", "Columns (* = needed):",
                *[f"{c.heading}{' *' if c.required else ''}: {c.help or c.kind}" for c in self.columns],
                "", "Importing again updates the rows that match (see above) instead of adding them twice."]


def by_name(rows: list[dict], field_: str = "name") -> dict[str, dict]:
    return {str(r.get(field_) or "").strip().lower(): r for r in rows if r.get(field_)}


def find(index: dict, name, what: str) -> dict | None:
    if not name:
        return None
    hit = index.get(str(name).strip().lower())
    if hit is None:
        raise ValueError(f"No {what} called {name!r}")
    return hit
