#!/usr/bin/env python3

import asyncio
import os
import sys

from mitmproxy import options
from mitmproxy.tools.dump import DumpMaster


def main():
    if len(sys.argv) != 4:
        print('Usage: proxy_runner.py <port> <log_file> <verbosity>')
        sys.exit(1)

    port = int(sys.argv[1])
    log_file = sys.argv[2]
    int(sys.argv[3])

    # Import addon here to avoid circular imports
    from five_cli.proxy.addon import ClaudeInterceptor

    # Set up mitmproxy options
    opts = options.Options(listen_port=port, listen_host='127.0.0.1')

    # Configure Five paths - these should come from environment or config
    five_config_path = os.path.join(os.getcwd(), '.five', 'config.json')
    project_path = os.getcwd()

    # Create interceptor with proper paths
    interceptor = ClaudeInterceptor(log_file, five_config_path, project_path)

    # Create and run the proxy
    async def run_proxy():
        master = DumpMaster(opts)
        master.addons.add(interceptor)
        try:
            await master.run()
        except KeyboardInterrupt:
            pass
        finally:
            master.shutdown()

    asyncio.run(run_proxy())


if __name__ == '__main__':
    main()
