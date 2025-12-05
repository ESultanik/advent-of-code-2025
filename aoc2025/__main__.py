import sys

from .cli import main as cli_main


def main():
    sys.exit(cli_main(sys.argv))


if __name__ == '__main__':
    main()
