import aiohttp
import argparse
import asyncio
import logging
import shlex
import sys
from lxml import etree

from sans import Api, HTTPException, run_in_thread, __version__


logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        allow_abbrev=False,
        description="SANS Console Entry",
        prog="sans",
        epilog="Any unknown args will be used to build the API request.",
    )
    parser.add_argument("--version", action="version", version="%(prog)s " + __version__)
    parser.add_argument("--agent", help="set the script's user agent")
    parser.add_argument(
        "--quit", action="store_true", help="quit the console program loop after this run"
    )
    parser.usage = parser.format_usage() + " ..."
    known, unknown = parser.parse_known_args()
    if not any(vars(known).values()):
        parser.print_help(sys.stderr)
    run_in_thread()
    if known.quit and not unknown:
        return print("Okay I'll just leave I guess...", file=sys.stderr)
    Api.agent = known.agent or input("User agent: ")
    args = ()
    while True:
        print()
        if not args and unknown:
            args = (known, unknown)
        else:
            args = parser.parse_known_args(shlex.split(input(parser.prog + " ")))
            if args[0].agent:
                print("You can't change the agent in the middle of the script.", file=sys.stderr)
        known, unknown = args
        if not unknown:
            if known.quit:
                return print("No query provided. Exiting...", file=sys.stderr)
            print("No query provided.", file=sys.stderr)
            parser.print_usage(sys.stderr)
            continue
        request = {}
        key = "q"
        for arg in unknown:
            if arg.startswith("--"):
                if key != "q":
                    print("No value provided for key {!r}".format(key), file=sys.stderr)
                    continue
                key = arg[2:]
            else:
                request.setdefault(key, []).append(arg)
                key = "q"
        if key != "q":
            print("No value provided for key {!r}".format(key), file=sys.stderr)
            continue
        request = Api(request)
        try:
            for element in request.threadsafe:
                print(element.to_pretty_string(), end="")
        except HTTPException as e:
            print(e, file=sys.stderr)
        except Exception as e:
            logging.exception(e)
        if known.quit:
            return print("Exiting...", file=sys.stderr)


if __name__ == "__main__":
    main()
