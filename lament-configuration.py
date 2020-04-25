import os

from lc.app import app
import lc.config
import lc.model

lc.config.app.init_db()
lc.model.create_tables()
