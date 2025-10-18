from pathlib import Path
import tempfile
from click.testing import CliRunner
from five_cli.cli.main import cli

runner = CliRunner()

print("Test 1: First setup")
with tempfile.TemporaryDirectory() as td1:
    config_path1 = Path(td1)
    result1 = runner.invoke(cli, ['setup', '--config', str(config_path1)])
    print(f"Result 1 exit code: {result1.exit_code}")
    if result1.exit_code != 0:
        print(f"Output 1: {result1.output}")

print("\nTest 2: Second setup")
with tempfile.TemporaryDirectory() as td2:
    config_path2 = Path(td2)
    result2 = runner.invoke(cli, ['setup', '--config', str(config_path2)])
    print(f"Result 2 exit code: {result2.exit_code}")
    if result2.exit_code != 0:
        print(f"Output 2: {result2.output}")

print("\nTest 3: Third setup")
with tempfile.TemporaryDirectory() as td3:
    config_path3 = Path(td3)
    result3 = runner.invoke(cli, ['setup', '--config', str(config_path3)])
    print(f"Result 3 exit code: {result3.exit_code}")
    if result3.exit_code != 0:
        print(f"Output 3: {result3.output}")
