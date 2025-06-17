from invoke import task


@task
def black(c):
    c.run("black .")


@task
def isort(c):
    c.run("isort .")


@task(black, isort)
def lint(_):
    pass

@task
def test(c):
    c.run("uv run python -m unittest discover -s tests/")

