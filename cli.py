import click

from core.app import run_local_shell


@click.group()
def five_cli():
    pass


@five_cli.command()
def init():
    click.echo("Initializing Five project... (not implemented)")


@five_cli.command()
@click.argument(
    "directory",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, readable=True),
    default=".",
)
def index(directory: str):
    click.echo(f"Indexing directory: {directory} (not implemented)")


@five_cli.command()
def shell():
    run_local_shell()


@five_cli.command()
def search():
    print("Search command called without query. (not implemented)")


if __name__ == "__main__":
    five_cli()
