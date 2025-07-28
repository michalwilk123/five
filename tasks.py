from invoke import task


@task
def ruff(c):
    c.run("ruff format indexer")

@task(ruff)
def lint(_):
    pass

@task
def ctags(c):
    c.run("ctags -R --languages=Python --exclude=test_repositories")

@task
def test(c):
    c.run("uv run python -m unittest discover -v -s indexer/tests/")
