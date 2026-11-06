import sys


def is_console():
    if len(sys.argv) > 1:
        # Finder's legacy process argument is not a CLI option.
        return sys.argv[1].startswith("-") and not sys.argv[1].startswith("-psn_")
    return sys.stdin is not None and sys.stdin.isatty()


if __name__ == "__main__":
    if is_console():
        from sd_prompt_reader.cli import cli

        cli()
    else:
        from sd_prompt_reader.app import main

        main()
