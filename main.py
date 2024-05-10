from sd_prompt_reader.app import main
from sd_prompt_reader.cli import cli
import sys


def is_console():
    return False if sys.stdin is None else sys.stdin.isatty()


if __name__ == "__main__":
    if is_console():
        cli()
    else:
        main()
