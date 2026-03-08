from datetime import datetime
from invoke import task


@task
def test(c):
    """Run all the provided tests"""
    c.run("uv run python -m pytest tests/*.py -W ignore::DeprecationWarning")


@task
def webpack(c):
    """Run the webpack build"""
    c.run("pnpm webpack")


@task(webpack)
def run(c, port=8080, host="127.0.0.1"):
    """Run a debug server locally"""
    c.run(
        f"uv run python -m flask run -p {port} -h {host}",
        env={
            "FLASK_APP": "lament-configuration.py",
            "LC_APP_PATH": f"http://{host}:{port}",
            "LC_DB_PATH": "test.db",
            "LC_SECRET_KEY": "TESTING_KEY",
        },
    )


@task
def migrate(c, port=8080, host="127.0.0.1"):
    """Run migrations to update the database schema"""
    c.run(
        "uv run python scripts/migrate.py",
        env={
            "FLASK_APP": "lament-configuration.py",
            "LC_APP_PATH": f"http://{host}:{port}",
            "LC_DB_PATH": "test.db",
            "LC_SECRET_KEY": "TESTING_KEY",
        },
    )


@task
def install(c):
    """Install the listed dependencies into a virtualenv"""
    c.run("pnpm install")


@task
def fmt(c):
    """Automatically format the source code, committing it if it is safe to do so."""
    status = c.run("git status --porcelain", hide="stdout")
    is_clean = status.stdout.strip() == ""
    c.run("uv run black $(find lc scripts stubs tests *.py -name '*.py')")
    c.run("pnpm exec prettier --write .")

    if is_clean:
        date = datetime.now().isoformat()
        c.run(f"git commit -a -m 'Automatic formatting commit: {date}'")
    else:
        print("Uncommitted change exist; skipping commit")


@task
def checkfmt(c):
    """Automatically format the source code, committing it if it is safe to do so."""
    return c.run("pnpm exec prettier --check .") and c.run(
        "uv run black --check $(find lc scripts stubs tests *.py -name '*.py')"
    )


@task
def populate(c, port=8080, host="127.0.0.1"):
    """Populate the test database with fake-ish data"""
    c.run(
        "uv run python -s ./scripts/populate.py",
        env={
            "FLASK_APP": "lament-configuration.py",
            "LC_APP_PATH": f"http://{host}:{port}",
            "LC_DB_PATH": "test.db",
            "LC_SECRET_KEY": "TESTING_KEY",
        },
    )


@task
def tc(c):
    """Typecheck with mypy"""
    c.run("uv run mypy --check-untyped-defs lc/*.py tests/*.py scripts/*.py")


@task
def lint(c):
    """Lint with flake8"""
    c.run("uv run flake8")


@task
def docker(c, container_name="lc"):
    c.run(f"docker build . -t {container_name}")


@task(docker, populate)
def run_dev_server(c, port=8080):
    env_vars = {
        "LC_SECRET_KEY": "TESTING_KEY",
        "LC_DB_PATH": "/opt/run/test.db",
        "SOCKET": f":{port}",
    }
    env_vars = " ".join((f"-e {k}={v}" for (k, v) in env_vars.items()))
    c.run(f"docker run -t -i -v $(pwd):/opt/run {env_vars} -p {port}:{port} lc")
