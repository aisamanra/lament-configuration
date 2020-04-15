# Lament Configuration

[![Build Status](http://ci.infinitenegativeutility.com/api/badges/getty/lament-configuration/status.svg)](http://ci.infinitenegativeutility.com/getty/lament-configuration)

![lament configuration logo](/lc/static/lc_64.png)

Bookmark organizing for pinheads.

## In-Progress Screenshots

![screenshot 01](/screenshots/lament-configuration-inprogress-01.png)

## Planned Features

- [ ] Hierarchical tags: every link tagged with `#food/bread` will also be visible under `#food`
- [ ] Collections: your top-level view of links can optionally be several folder-like divisions instead of a single tagged soup of link
- [ ] Optional image previews: links can be viewed in text view or in thumbnail view, and this setting should be sticky on a per-collection basis
- [ ] Some kind of bookmarklet for adding links, of course

## Developing

You'll need `poetry` installed, and having `invoke` installed makes it easier.

```bash
# install all the needed dependencies
$ inv install
# run all the tests
$ inv test
# run a local test server at port 9999
$ inv run -p 9999
```

All the code here is auto-formatted by `black`, which should be installed by the `inv install`. Running `inv fmt` on a clean branch will run `black` over all Python files and commit those changes automatically; if the repository is dirty then it will run the formatter but won't try to commit anything.
