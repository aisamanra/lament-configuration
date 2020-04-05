import os

import playhouse.sqlite_ext

DB_LOC=os.getenv('SCRAPBOARD', 'test.db')
DB=playhouse.sqlite_ext.SqliteExtDatabase(DB_LOC)
