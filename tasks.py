from invoke import task


@task
def black(c):
    print("Running black...")
    c.run('black . --extend-exclude "test_repositories"')


@task
def isort(c):
    c.run('isort . --extend-skip-glob "test_repositories"')


@task(black, isort)
def lint(_):
    pass


@task
def test(c):
    c.run("uv run python -m unittest discover -v -s indexer/tests/")
