# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Optional demo data: a taco business with two weeks of history, so every screen shows how the app works.

    scripts/run.sh demo ADMIN_EMAIL ADMIN_PASSWORD [--days 14]

ADMIN_EMAIL / ADMIN_PASSWORD: the platform admin made with `scripts/run.sh admin` (it creates the demo business).
The site and services must be running. Run it once: when "Demo Taco Co" exists it only prints the logins again.
Demo logins share one password (data.PASSWORD) - demo only, never for a real business.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import data  # noqa: E402
import history  # noqa: E402
import setup  # noqa: E402
import floor  # noqa: E402
import today  # noqa: E402
from api import ApiFailed, Site  # noqa: E402


def say(text: str) -> None:
    print(f"  · {text}", flush=True)


def logins() -> None:
    print(f"\nDemo logins (password for all: {data.PASSWORD})")
    rows = [("Owner - sees everything", data.OWNER["email"])] + [(f"{name} ({role})", email) for role, name, email in data.STAFF]
    for label, email in rows:
        print(f"  {email:28} {label}")
    print("As the platform admin: Businesses -> Demo Taco Co -> Open, to look at it as support.\n")


def main(args: list[str]) -> int:
    if len(args) < 2 or args[0] in ("-h", "--help"):
        print(__doc__)
        return 1
    days = int(args[args.index("--days") + 1]) if "--days" in args else 14
    site = Site()
    try:
        site.login("ops", args[0], args[1])
        if any(b["name"] == data.BUSINESS["name"] for b in site.get("/platform/businesses", "ops")):
            print(f"{data.BUSINESS['name']} is already there - nothing added.")
            logins()
            return 0
        print(f"Creating {data.BUSINESS['name']} with {days} days of history (a few minutes)...")
        ids = setup.create(site, args[0], args[1], say)
        history.run(site, ids, days, say)
        today.run(site, ids, say)
        floor.run(site, ids, say)
    except (ApiFailed, RuntimeError) as e:
        print(f"demo stopped: {e}")
        return 1
    print("Done.")
    logins()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
