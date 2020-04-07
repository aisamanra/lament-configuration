from datetime import datetime
from invoke import task


@task
def test(c):
    """Run all the provided tests"""
    c.run("poetry run python -m pytest tests/*.py")


@task
def run(c, port=8080, host="127.0.0.1"):
    """Run a debug server locally"""
    c.run(
        f"poetry run python -m flask run -p {port} -h {host}",
        env={"FLASK_APP": "lament-configuration.py"},
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
    c.run("poetry run black $(find . -name '*.py')")

    if is_clean:
        date = datetime.now().isoformat()
        c.run(f"git commit -a -m 'Automatic formatting commit: {date}'")
    else:
        print("Uncommitted change exist; skipping commit")


@task
def populate(c):
    """Populate the test database with fake-ish data"""
    c.run("PYTHONPATH=$(pwd) poetry run python3 ./scripts/populate.py")
