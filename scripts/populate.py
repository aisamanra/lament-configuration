#!/usr/bin/env python3

import datetime
import json

import lc.config
import lc.model as m
import lc.request as r


def main():
    lc.config.db.init("test.db")
    m.create_tables()

    u = m.User.get_or_none(name="gdritter")
    if not u:
        u = m.User.from_request(r.User(name="gdritter", password="behest",))
        u.set_as_admin()

    with open("scripts/aisamanra.json") as f:
        links = json.load(f)
    for l in links:
        time = datetime.datetime.strptime(l["time"], "%Y-%m-%dT%H:%M:%SZ")
        req = r.Link(
            url=l["href"],
            name=l["description"],
            description=l["extended"],
            private=l["shared"] == "yes",
            tags=l["tags"].split(),
            created=time,
        )
        print(m.Link.from_request(u, req))


if __name__ == "__main__":
    main()
