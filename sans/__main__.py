#!/usr/bin/python3

from __future__ import annotations

import argparse
import shlex
import sys
import traceback
from typing import Any
from xml.etree import ElementTree as etree

import sans

try:
    from rich import print  # type: ignore
    from rich.syntax import Syntax  # type: ignore
except ImportError:

    def Syntax(arg: Any, *_: Any, **__: Any) -> Any:
        return arg


def main() -> None:
    parser = argparse.ArgumentParser(
        allow_abbrev=False,
        description="SANS Console Entry",
        prog="sans",
        epilog="Any unknown args will be used to build the API request.",
    )
    parser.add_argument(
        "--version", action="version", version="%(prog)s " + sans.__version__
    )
    parser.add_argument("--agent", help="set the script's user agent")
    parser.add_argument(
        "--quit",
        action="store_true",
        help="quit the console program loop after this run",
    )
    parser.usage = parser.format_usage() + " ..."
    known, unknown = parser.parse_known_args()
    if not any(vars(known).values()):
        parser.print_help(sys.stderr)
    if known.quit and not unknown:
        print("Okay, I'll just leave I guess...", file=sys.stderr)
        return
    sans.set_agent(known.agent or input("User agent: "))
    args: tuple[argparse.Namespace, list[str]] | tuple[()] = ()
    with sans.Client() as client:
        while True:
            print()
            if not args and unknown:
                args = (known, unknown)
            else:
                args = parser.parse_known_args(shlex.split(input(parser.prog + " ")))
                if args[0].agent:
                    print(
                        "You can't change the agent in the middle of the script.",
                        file=sys.stderr,
                    )
            known, unknown = args
            if not unknown:
                if known.quit:
                    print("No query provided. Exiting...", file=sys.stderr)
                    return
                print("No query provided.", file=sys.stderr)
                parser.print_usage(sys.stderr)
                continue
            parameters: dict[str, list[str]] = {}
            key = "q"
            for arg in unknown:
                if arg.startswith("--"):
                    if key != "q":
                        print(
                            "No value provided for key {!r}".format(key),
                            file=sys.stderr,
                        )
                        continue
                    key = arg[2:]
                else:
                    parameters.setdefault(key, []).append(arg)
                    key = "q"
            if key != "q":
                print("No value provided for key {!r}".format(key), file=sys.stderr)
                continue
            try:
                with client.stream("GET", sans.API_URL, params=parameters) as response:
                    print(response.url, end="\n\n")
                    for element in response.iter_xml():
                        pretty_print(element)
            except Exception:
                traceback.print_exc()
            if known.quit:
                print("Exiting...", file=sys.stderr)
                return


def pretty_print(element: etree.Element) -> None:
    sans.indent(element)
    print(Syntax(etree.tostring(element, encoding="unicode").strip(), "xml"))


if __name__ == "__main__":
    main()
