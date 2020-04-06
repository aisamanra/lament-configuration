import os

import lc.config
import lc.model
import lc.routes

lc.config.DB.init(os.getenv("DB_LOC", "test.db"))
lc.model.create_tables()
app = lc.routes.app
