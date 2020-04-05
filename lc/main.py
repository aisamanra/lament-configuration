import os

import lc.config
import lc.routes

lc.config.DB.init(os.getenv("DB_LOC", "test.db"))
app = lc.routes.app
