from sd_prompt_reader.app import main
from sd_prompt_reader.cli import cli
import sys

if __name__ == "__main__":
    if sys.stdin.isatty():
        cli()
    else:
        main()
