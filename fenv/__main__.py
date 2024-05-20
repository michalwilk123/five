"""
The Five environment

The system conversation capability of Five
Main purpose of this part is the way to inspect and
view the history of changes (something like semantic
version control system). Made to easily extendable like
tox, maven, make

The user creates a conversations, named scenarios that
define the system requirements constrained by the system
"""
import argparse
from colorama import init, Fore

# Initialize colorama to support coloring terminal text
init(autoreset=True)

def main(positional_arg, keyword_arg1=None, keyword_arg2=None):
    """
    Main function that takes positional and keyword arguments.
    """
    print(f"Positional Argument: {Fore.GREEN}{positional_arg}{Fore.RESET}")
    print(f"Keyword Argument 1: {Fore.BLUE}{keyword_arg1}{Fore.RESET}")
    print(f"Keyword Argument 2: {Fore.YELLOW}{keyword_arg2}{Fore.RESET}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Program with positional and keyword arguments")
    parser.add_argument("positional_arg", help="This is a positional argument")
    parser.add_argument("--keyword_arg1", help="This is a keyword argument 1")
    parser.add_argument("--keyword_arg2", help="This is a keyword argument 2")
    args = parser.parse_args()

    main(args.positional_arg, args.keyword_arg1, args.keyword_arg2)

