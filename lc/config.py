import os
import sys

import flask
import itsdangerous
import playhouse.sqlite_ext

db = playhouse.sqlite_ext.SqliteExtDatabase(None)
per_page = 50
serializer = itsdangerous.URLSafeSerializer("TEMP KEY")
app = flask.Flask(__name__)
app.secret_key = "ARGLBARGL"

if sys.stderr.isatty():

    def log(msg):
        sys.stderr.write(str(msg))
        sys.stderr.write("\n")


else:

    def log(msg):
        sys.stderr.write("\x1b[31m")
        sys.stderr.write(str(msg))
        sys.stderr.write("\x1b[39m\n")
