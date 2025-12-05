import argparse
from pathlib import Path
import sys
from tempfile import NamedTemporaryFile
from typing import Optional

from . import CHALLENGES, Challenge


def validate(challenge: Challenge) -> bool:
    errored = False
    for i, example in enumerate(challenge.examples):
        if example.skip:
            print(f"\t\tExample {i + 1}: ⏩ (skipped)")
            continue
        try:
            challenge.validate(example)
            print(f"\t\tExample {i + 1}: ✅")
        except ValueError as e:
            print(f"\t\tExample {i + 1}: ❌")
            print(f"\t\t{e!s}")
            errored = True
    return not errored


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Evan Sultanik's Advent of Code Solutions")

    parser.add_argument("INPUT", type=Path, nargs="?", default=Path("-"),
                        help="path to the input file (default is STDIN)")
    challenge_group = parser.add_mutually_exclusive_group(required=True)
    challenge_group.add_argument("--day", "-d", type=int, choices=sorted(CHALLENGES.keys()),
                                 help="the day number")
    challenge_group.add_argument("--list", "-l", action="store_true", help="list all available challenges")
    challenge_group.add_argument("--latest", action="store_true",
                                 help="run the latest part of the latest challenge; if no input is provided and an "
                                      "associated `day#.txt` is available, use that as input")
    challenge_group.add_argument("--validate", "-v", action="store_true",
                                 help="validate a challenge by running any and all examples")
    parser.add_argument("--part", "-p", type=int, default=-1, help="the part of the challenge to run; if "
                                                                   "the part is negative, then all parts for the given "
                                                                   "day will be run (default=-1)")
    parser.add_argument("--output", "-o", type=str,
                        help="path to the output file, or '-' for STDOUT (the default)",
                        default="-")

    args = parser.parse_args()

    if hasattr(args, "list") and args.list:
        for day, parts in sorted(CHALLENGES.items()):
            if not parts:
                continue
            print(f"Day {day}:")
            for i, part in parts.items():
                print(f"\tPart {i}:\t{part.__name__}")
        return 0
    elif hasattr(args, "validate") and args.validate:
        errored = False
        for day, parts in sorted(CHALLENGES.items()):
            if not parts:
                continue
            print(f"Day {day}:")
            for i, part in parts.items():
                print(f"\tPart {i}:\t{part.__name__}")
                if not validate(challenge=part):
                    errored = True
        if not errored:
            return 0
        else:
            return 1

    infile: Optional[Path] = None

    if hasattr(args, "latest") and args.latest:
        if not CHALLENGES:
            sys.stderr.write("Error: There are no challenges implemented!\n")
            return 1
        latest_day = max(CHALLENGES.keys())
        latest = CHALLENGES[latest_day]
        latest_part = max(latest.keys())
        latest_challenge = latest[latest_part]
        parts = [(latest_part, latest_challenge)]
        if args.INPUT.name == "-":
            latest_input_path = Path(f"day{latest_day}.txt")
            if latest_input_path.exists():
                sys.stderr.write(f"Using input {latest_input_path!s}\n")
                infile = latest_input_path
            elif latest_challenge.examples:
                print(f"Validating Examples for Day {latest_day}:")
                print(f"\tPart {latest_part}: {latest_challenge.__name__}")
                if validate(latest_challenge):
                    return 0
                else:
                    return 1
            else:
                print("Reading input from STDIN...")
        setattr(args, "day", latest_day)
    elif args.day not in CHALLENGES:
        sys.stderr.write(f"Unknown day: {args.day}\n")
        return 1
    elif args.part < 0:
        parts = sorted(CHALLENGES[args.day].items())
    elif args.part not in CHALLENGES[args.day]:
        sys.stderr.write(f"Day {args.day} does not have part {args.part}\n")
        return 1
    else:
        parts = [(args.part, CHALLENGES[args.day][args.part])]

    delete_on_exit = False
    if infile is None:
        if args.INPUT.name == "-":
            tmpfile = NamedTemporaryFile("w", delete=False)
            tmpfile.write(sys.stdin.read())
            tmpfile.close()
            infile = Path(tmpfile.name)
            delete_on_exit = True
        else:
            infile = args.INPUT

    if args.output == "-":
        outfile = sys.stdout
    else:
        outfile = open(args.output, "w")

    try:
        if sys.stderr.isatty() and outfile.isatty():
            sys.stderr.write(f"Day {args.day}\n")
        for part, func in parts:
            if sys.stderr.isatty() and outfile.isatty():
                sys.stderr.write(f"Running {func.__name__}...\n")
            result = func(infile)
            if sys.stderr.isatty() and outfile.isatty():
                sys.stderr.write(f"Part {part}: ")
                sys.stderr.flush()
            outfile.write(f"{result!s}\n")
            outfile.flush()

    finally:
        if delete_on_exit:
            infile.unlink()
        if outfile != sys.stdout:
            outfile.close()

    return 0
