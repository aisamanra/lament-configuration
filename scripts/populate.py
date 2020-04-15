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

    tags = {}
    for l in links:
        for t in l["tags"].split():
            if t in tags:
                continue

            tags[t] = m.Tag.get_or_create_tag(u, t)

    with c.db.atomic():
        for l in links:
            time = datetime.datetime.strptime(l["time"], "%Y-%m-%dT%H:%M:%SZ")
            ln = m.Link.create(
                url=l["href"],
                name=l["description"],
                description=l["extended"],
                private=l["shared"] == "no",
                created=time,
                user=u,
            )
            for t in l["tags"].split():
                m.HasTag.create(link=ln, tag=tags[t])
            c.log(f"created link {ln.url}")


if __name__ == "__main__":
    main()
