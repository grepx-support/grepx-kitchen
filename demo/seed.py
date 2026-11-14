# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Optional demo data: two businesses with two weeks of history, so every screen shows how the app works -
Demo Taco Co (Sydney, AUD; data.py) and Spice Route Kitchen (an Indian restaurant group in Mumbai, INR; india.py).

    scripts/run.sh demo ADMIN_EMAIL ADMIN_PASSWORD [--days 14] [--only taco|india] [--resume]

ADMIN_EMAIL / ADMIN_PASSWORD: the platform admin made with `scripts/run.sh admin` (it creates the demo businesses).
The site and services must be running. A demo business that already exists is left alone (its logins are printed again);
with --resume its last steps (deliveries, warehouse floor, money) run again - to finish one that stopped half way.
Demo logins share one password (data.PASSWORD) - demo only, never for a real business.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import data  # noqa: E402
import india  # noqa: E402
import history  # noqa: E402
import setup  # noqa: E402
import floor  # noqa: E402
import funds  # noqa: E402
import money  # noqa: E402
import safety  # noqa: E402
import team  # noqa: E402
import today  # noqa: E402
from api import ApiFailed, Site  # noqa: E402


def say(text: str) -> None:
    print(f"  · {text}", flush=True)


PROFILES = {"taco": data, "india": india}


def logins(d) -> None:
    print(f"\n{d.BUSINESS['name']} ({d.BUSINESS['currency']}) - logins, password for all: {d.PASSWORD}")
    rows = [("Owner - sees everything", d.OWNER["email"])] + [(f"{name} ({role})", email) for role, name, email in d.STAFF]
    for label, email in rows:
        print(f"  {email:30} {label}")


def one(site, d, args: list[str], days: int, resume: bool = False) -> None:
    if any(b["name"] == d.BUSINESS["name"] for b in site.get("/platform/businesses", "ops")):
        if not resume:
            print(f"{d.BUSINESS['name']} is already there - nothing added.")
            return
        print(f"Finishing {d.BUSINESS['name']}...")
        ids = setup.existing(site, d)
        today.deliveries(site, d, ids, say)
        floor.run(site, d, ids, say)
        money.run(site, d, ids, say)
        return
    print(f"Creating {d.BUSINESS['name']} with {days} days of history (a few minutes)...")
    ids = setup.create(site, d, args[0], args[1], say)
    history.run(site, d, ids, days, say)
    today.run(site, d, ids, say)
    floor.run(site, d, ids, say)
    money.run(site, d, ids, say)
    team.run(site, d, ids, say)
    safety.run(site, d, ids, say)
    funds.run(site, d, ids, say)


def main(args: list[str]) -> int:
    if len(args) < 2 or args[0] in ("-h", "--help"):
        print(__doc__)
        return 1
    days = int(args[args.index("--days") + 1]) if "--days" in args else 14
    only = args[args.index("--only") + 1] if "--only" in args else ""
    if only and only not in PROFILES:
        print(f"--only takes one of: {', '.join(PROFILES)}")
        return 1
    chosen = [PROFILES[only]] if only else list(PROFILES.values())
    site = Site()
    try:
        site.wait_until_up()
        for d in chosen:
            site.login("ops", args[0], args[1])
            one(site, d, args, days, "--resume" in args)
    except (ApiFailed, RuntimeError) as e:
        print(f"demo stopped: {e}")
        return 1
    print("Done.")
    for d in chosen:
        logins(d)
    print("\nAs the platform admin: Businesses -> (a demo business) -> Open, to look at it as support.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
