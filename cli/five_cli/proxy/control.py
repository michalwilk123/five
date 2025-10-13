import argparse
import sys

from five_cli.cli.server import setup_logging, start_proxy, status_proxy, stop_proxy
from five_cli.utils.net import find_running_proxy

DEFAULT_PORT = 8089


def build_parser():
    p = argparse.ArgumentParser(prog='five-proxy', description='Claude proxy server manager')
    p.add_argument('-v', '--verbose', action='count', default=0)
    sub = p.add_subparsers(dest='command', required=True)

    sp_start = sub.add_parser('start')
    sp_start.add_argument('--port', type=int)
    sp_start.add_argument('--log-file', type=str, default='claude_proxy.log')

    sub.add_parser('stop')
    sub.add_parser('status')

    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    setup_logging(args.verbose)

    if args.command == 'start':
        found = find_running_proxy(DEFAULT_PORT, 100)
        if found:
            print(f'Proxy already running on port {found}')
            return 0

        ok = start_proxy(args.port, args.log_file, args.verbose, print)
        return 0 if ok else 1

    elif args.command == 'stop':
        ok = stop_proxy(print)
        return 0 if ok else 1

    elif args.command == 'status':
        ok = status_proxy(print)
        return 0 if ok else 1

    return 1


if __name__ == '__main__':
    sys.exit(main())
