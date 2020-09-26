from lc.app import app  # noqa: F401
import lc.config
import lc.model

lc.config.app.init_db()
lc.model.create_tables()
