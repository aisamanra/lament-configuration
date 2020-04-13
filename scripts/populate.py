#!/usr/bin/env python3

import datetime
import json
import os

import lc.config as c
import lc.model as m
import lc.request as r


def main():
    c.db.init("test.db")
    m.create_tables()

    u = m.User.get_or_none(name="gdritter")
    if not u:
        u = m.User.from_request(
            r.User(name="gdritter", password=os.getenv("PASSWORD", "behest").strip(),)
        )
        u.set_as_admin()

    c.log(f"created user {u.name}")

    with open("scripts/aisamanra.json") as f:
        links = json.load(f)
    for l in links:
        time = datetime.datetime.strptime(l["time"], "%Y-%m-%dT%H:%M:%SZ")
        req = r.Link(
            url=l["href"],
            name=l["description"],
            description=l["extended"],
            private=l["shared"] == "no",
            tags=l["tags"].split(),
            created=time,
        )
        l = m.Link.from_request(u, req)
        c.log(f"created link {l.url}")


if __name__ == "__main__":
    main()
