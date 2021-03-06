# Lament Configuration

[![Build Status](https://ci.infinitenegativeutility.com/api/badges/getty/lament-configuration/status.svg)](https://ci.infinitenegativeutility.com/getty/lament-configuration)

![lament configuration logo](/static/lc_64.png)

Bookmark organizing for pinheads. Lament Configuration is [primarily developed on a self-hosted Gogs instance](https://git.infinitenegativeutility.com/getty/lament-configuration) but is [mirrored on Github](https://github.com/aisamanra/lament-configuration) for easier issue reporting.

Lament Configuration is a barebones [Pinboard](https://pinboard.in/)-like bookmark organizing service. It's currently in unstable alpha state, but current features include:
- The ability to create, edit, and delete lists of links along with their metadata
- A tagging system for categorizing and retrieving links.
    - Lament-Configuration tags are always _hierarchical_: the tag `#food/bread` implies the tag `#food`
    - Hierarchical tags are also displayed in a "unix-like" way, i.e. two tags `#book/scifi` and `#book/fantasy` will be rendered together as `#book/{scifi,fantasy}`.
- A work-in-progress REST API
- Multi-user support via manual invitation links
- A bookmarklet to easily add new links

## In-Progress Screenshots

![screenshot 02](/screenshots/lament-configuration-inprogress-02.png)

## Planned Features

The following features are planned but not yet implemented.
- Cleaner design and better responsibity, but also graceful degradation in the face of disabled JavaScript.
- A stable and expressive REST API.
- Better admin features, including the ability to bless secondary admins.
- Richer tag search, with boolean operations and the like.
- Collections: your top-level view of links can optionally be presented as several folder-like divisions instead of an amorphous soup of links.
- Optional image previews: links can be viewed in text view or in thumbnail view, and this setting should be sticky on a per-collection basis.

Some features are missing on purpose. Lament Configuration is intended to be [anti-capitalist, human-scale software](https://medium.com/@jkriss/anti-capitalist-human-scale-software-and-why-it-matters-5936a372b9d): it will never attempt to scale to hundreds of users in terms of either technical limitations or features. For example, adding new users to Lament Configuration currently works by way of single-use invite links, and I am not planning on adding open user registration as a feature: manual invite links allows an administrator to add users on a case-by-base basis, but still requires manual intervention and conscious choice when extending a Lament Configuration instance to new users.

## Developing

See the [notes on developing lament-configuration](DEVELOPING.md).

## Contributors

- [Getty](https://twitter.com/aisamanra)
- [Trevor](https://twitter.com/moltarx)
