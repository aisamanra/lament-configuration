import os

os.environ["LC_DB_PATH"] = ":memory:"
os.environ["LC_SECRET_KEY"] = "TEST_KEY"
os.environ["LC_APP_PATH"] = "localhost"
