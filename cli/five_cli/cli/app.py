#!/usr/bin/env python3

import click

from five_cli.cli.code import code
from five_cli.cli.project import project
from five_cli.cli.server import server


@click.group()
@click.option('-v', '--verbose', is_flag=True, help='Verbose output')
@click.pass_context
def cli(ctx, verbose):
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose


cli.add_command(code)
cli.add_command(server)
cli.add_command(project)


if __name__ == '__main__':
    cli()
