import click

from five.cli.get import get
from five.cli.init import init
from five.cli.redo import redo
from five.cli.setup import setup
from five.cli.track import track
from five.cli.undo import undo


@click.group()
@click.pass_context
def cli(_ctx: click.Context):
    pass


cli.add_command(get)
cli.add_command(init)
cli.add_command(redo)
cli.add_command(setup)
cli.add_command(track)
cli.add_command(undo)


if __name__ == '__main__':
    cli()
