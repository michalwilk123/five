import argparse


def run():
    parser = argparse.ArgumentParser(
        description="A simple CLI for handling 'template' and 'project' arguments with an optional 'verbose' flag."
    )

    # Positional or keyword arguments
    parser.add_argument("template", type=str, help="The template to use")
    parser.add_argument("project", type=str, help="The project name", nargs="?")

    # Optional argument
    parser.add_argument(
        "--verbose", action="store_true", help="Increase output verbosity"
    )

    args = parser.parse_args()

    # Display the parsed arguments
    # print(f"Template: {args.template}")
    # print(f"Project: {args.project}")

    if args.verbose:
        print("Verbose mode enabled")
