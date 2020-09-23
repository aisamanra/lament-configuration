from datetime import datetime
from invoke import task


@task
def test(c):
    """Run all the provided tests"""
    c.run("poetry run python -m pytest tests/*.py -W ignore::DeprecationWarning")


@task
def run(c, port=8080, host="127.0.0.1"):
    """Run a debug server locally"""
    c.run(
        f"poetry run python -m flask run -p {port} -h {host}",
        env={
            "FLASK_APP": "lament-configuration.py",
            "LC_APP_PATH": f"http://{host}:{port}",
            "LC_DB_PATH": f"test.db",
            "LC_SECRET_KEY": f"TESTING_KEY",
        },
    )


@task
def migrate(c, port=8080, host="127.0.0.1"):
    """Run migrations to update the database schema"""
    c.run(
        f"PYTHONPATH=$(pwd) poetry run python3 scripts/migrate.py",
        env={
            "FLASK_APP": "lament-configuration.py",
            "LC_APP_PATH": f"http://{host}:{port}",
            "LC_DB_PATH": f"test.db",
            "LC_SECRET_KEY": f"TESTING_KEY",
        },
    )


@task
def install(c):
    """Install the listed dependencies into a virtualenv"""
    c.run("poetry install")


@task
def fmt(c):
    """Automatically format the source code, committing it if it is safe to do so."""
    status = c.run("git status --porcelain", hide="stdout")
    is_clean = status.stdout.strip() == ""
    c.run("poetry run black $(find lc scripts stubs tests *.py -name '*.py')")

    if is_clean:
        date = datetime.now().isoformat()
        c.run(f"git commit -a -m 'Automatic formatting commit: {date}'")
    else:
        print("Uncommitted change exist; skipping commit")


@task
def checkfmt(c):
    """Automatically format the source code, committing it if it is safe to do so."""
    return c.run(
        "poetry run black --check $(find lc scripts stubs tests *.py -name '*.py')"
    )


@task
def populate(c):
    """Populate the test database with fake-ish data"""
    c.run("PYTHONPATH=$(pwd) poetry run python3 ./scripts/populate.py")


@task
def tc(c):
    """Typecheck with mypy"""
    c.run(
        "MYPYPATH=$(pwd)/stubs poetry run mypy --check-untyped-defs lc/*.py tests/*.py scripts/*.py"
    )

@task
def lint(c):
    """Typecheck with mypy"""
    c.run(
        "poetry run flake8"
    )


@task
def uwsgi(c, sock="lc.sock"):
    """Run a uwsgi server"""
    c.run(
        f"poetry run uwsgi --socket {sock} --module lament-configuration:app --processes 4 --threads 2"
    )
