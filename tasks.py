from invoke import task

@task
def test(c):
    '''Run all the provided tests'''
    c.run('poetry run python -m pytest tests/*.py')

@task
def run(c, port=8080, host='127.0.0.1'):
    '''Run a debug server locally'''
    c.run(
        f'poetry run python -m flask run -p {port} -h {host}',
        env={'FLASK_APP': 'lc/main.py'},
    )

@task
def install(c):
    '''Install the listed dependencies into a virtualenv'''
    c.run('poetry install')
