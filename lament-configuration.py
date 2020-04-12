import os

from lc.app import app
import lc.config
import lc.model

lc.config.db.init(os.getenv("DB_LOC", "test.db"))
lc.model.create_tables()
