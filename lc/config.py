from dataclasses import dataclass
import os
import sys
from typing import Any

import environ
import flask
import itsdangerous
import playhouse.sqlite_ext


@environ.config(prefix="LC")
class Config:
    secret_key = environ.var()
    app_path = environ.var()
    db_path = environ.var()
    static_path = environ.var("static")


@dataclass
class App:
    config: Config
    app: flask.Flask
    db: playhouse.sqlite_ext.SqliteExtDatabase
    serializer: itsdangerous.URLSafeTimedSerializer
    per_page: int = 50

    @staticmethod
    def from_env() -> "App":
        config = environ.to_config(Config)
        app = flask.Flask(
            __name__, static_folder=os.path.join(os.getcwd(), config.static_path),
        )
        app.secret_key = config.secret_key
        return App(
            config=config,
            db=playhouse.sqlite_ext.SqliteExtDatabase(None),
            serializer=itsdangerous.URLSafeTimedSerializer(config.secret_key),
            app=app,
        )

    def init_db(self):
        self.db.init(self.config.db_path)

    def in_memory_db(self):
        try:
            self.db.close()
        except:
            pass
        self.db.init(":memory:")

    def close_db(self):
        self.db.close()

    def serialize_token(self, obj: Any) -> str:
        return self.serializer.dumps(obj)

    def load_token(self, token: str) -> Any:
        return self.serializer.loads(token)


app = App.from_env()

if sys.stderr.isatty():

    def log(msg):
        sys.stderr.write(str(msg))
        sys.stderr.write("\n")


else:

    def log(msg):
        sys.stderr.write("\x1b[31m")
        sys.stderr.write(str(msg))
        sys.stderr.write("\x1b[39m\n")
