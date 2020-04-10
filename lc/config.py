import os
import sys

import itsdangerous
import playhouse.sqlite_ext

DB = playhouse.sqlite_ext.SqliteExtDatabase(None)
PER_PAGE = 50
SERIALIZER = itsdangerous.URLSafeSerializer('TEMP KEY')

if sys.stderr.isatty():

    def log(msg):
        sys.stderr.write(str(msg))
        sys.stderr.write("\n")


else:

    def log(msg):
        sys.stderr.write("\x1b[31m")
        sys.stderr.write(str(msg))
        sys.stderr.write("\x1b[39m\n")
