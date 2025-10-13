# Five CLI

CLI wrapper and proxy manager for Claude with mitmproxy integration.

## Installation

### Local Development Installation

To install the Five CLI locally for development:

1. **Clone and navigate to the project directory:**
   ```bash
   cd /path/to/five-test/cli
   ```

2. **Build the package using uv:**
```bash
uv build
```
This creates distribution files in the `dist/` directory.

3. **Install the built package:**
```bash
pip install dist/five_cli-0.1.0-py3-none-any.whl --force-reinstall
```

4. **Verify installation:**
```bash
five --help
```

### Alternative: Editable Installation

For active development where you want changes reflected immediately:

```bash
# Using virtual environment (recommended)
source .venv/bin/activate
uv pip install -e .

# Or using regular pip
pip install -e .
```

## Usage

The Five CLI provides three main commands:

- `five code` - Launch Claude Code with optional proxy support
- `five server` - Manage Claude proxy server (start, stop, status, restart)
- `five project` - Manage Five projects and version control

Run `five --help` or `five <command> --help` for detailed usage information.

## Dependencies

- Python >=3.12
- click >=8.2.1
- mitmproxy >=12.1.2

Note: mitmproxy has extensive dependencies for full proxy functionality including HTTP/2 support, cryptography, and web UI capabilities.