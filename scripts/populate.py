#!/usr/bin/env python3

import json

import lc.config
import lc.model as m
import lc.request as r


def main():
    lc.config.DB.init("test.db")
    u, _ = m.User.get_or_create(name="gdritter",)
    print(u)
    with open("scripts/aisamanra.json") as f:
        links = json.load(f)
    for l in links:
        req = r.Link(
            url=l["href"],
            name=l["description"],
            description=l["extended"],
            private=l["shared"] == "yes",
            tags=l["tags"].split(),
        )
        print(m.Link.from_request(u, req))


if __name__ == "__main__":
    main()
