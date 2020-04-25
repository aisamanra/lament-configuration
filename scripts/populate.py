#!/usr/bin/env python3

import datetime
import json
import os

import lc.config as c
import lc.model as m
import lc.request as r


def main():
    m.create_tables()

    u = m.User.get_or_none(name="gdritter")
    if not u:
        u = m.User.from_request(
            r.User(name="gdritter", password=os.getenv("PASSWORD", "behest").strip(),)
        )
        u.set_as_admin()

    c.log(f"created user {u.name}")

    with open("scripts/aisamanra.json") as f:
        u.import_pinboard_data(f)


if __name__ == "__main__":
    main()
