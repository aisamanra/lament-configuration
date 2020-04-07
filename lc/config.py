import os
import sys

import playhouse.sqlite_ext

DB = playhouse.sqlite_ext.SqliteExtDatabase(None)
PER_PAGE = 50

if sys.stderr.isatty():
    def log(msg, *args, **kwargs):
        sys.stderr.write(msg.format(*args, **kwargs))
        sys.stderr.write("\n")
else:
    def log(msg, *args, **kwargs):
        sys.stderr.write("\x1b[31m")
        sys.stderr.write(msg.format(*args, **kwargs))
        sys.stderr.write("\x1b[39m\n")
