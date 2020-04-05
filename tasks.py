from invoke import task

@task
def test(c):
    c.run('poetry run python -m pytest tests/*.py')

@task
def run(c, port=8080, host='127.0.0.1'):
    c.run(
        f'poetry run python -m flask run -p {port} -h {host}',
        env={'FLASK_APP': 'lc/main.py'},
    )

@task
def install(c):
    c.run('poetry install')
