#!/usr/bin/python3

from __future__ import annotations

import argparse
import shlex
import sys
import traceback
from typing import TYPE_CHECKING, Any
from xml.etree import ElementTree as ET

import sans

try:
    if not TYPE_CHECKING:
        from rich import print  # type: ignore
        from rich.syntax import Syntax  # type: ignore
except ImportError:

    def Syntax(arg: Any, *_args: Any, **_kwargs: Any) -> Any:
        return arg


def main() -> None:
    parser = argparse.ArgumentParser(
        allow_abbrev=False,
        description="SANS Console Entry",
        prog=sans.__name__,
        epilog="Any unknown args will be used to build the API request.",
    )
    parser.add_argument("--agent", help="set the script's user agent")
    parser.add_argument(
        "--headers",
        action="store_true",
        help="print the headers of the server response",
    )
    parser.add_argument(
        "--quit",
        action="store_true",
        help="quit the console program loop after this run",
    )
    parser.add_argument(
        "--url", action="store_true", help="print the URL of the generated request"
    )
    parser.add_argument("--version", action="version", version=sans.__version__)
    input_: list[str] | None = None
    with sans.Client() as client:
        while True:
            print(file=sys.stderr)
            known, unknown = parser.parse_known_args(input_)
            try:
                if known.agent:
                    try:
                        sans.set_agent(known.agent)
                    except RuntimeError:
                        print(
                            "You can't change the agent in the middle of the script.",
                            file=sys.stderr,
                        )
                if not unknown:
                    if known.quit:
                        print("No query provided. Exiting...", file=sys.stderr)
                        return
                    print("No query provided.", file=sys.stderr)
                    parser.print_help(sys.stderr)
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
                        key = arg[2:]
                    else:
                        parameters.setdefault(key, []).append(arg)
                        key = "q"
                if key != "q":
                    print("No value provided for key {!r}".format(key), file=sys.stderr)
                with client.stream(
                    "GET",
                    sans.World(**{k: " ".join(v) for k, v in parameters.items()}),
                ) as response:
                    if known.url:
                        print(response.url, end="\n\n")
                    if known.headers:
                        print(response.headers, end="\n\n")
                    for element in response.iter_xml():
                        pretty_print(element)
                if known.quit:
                    print("Exiting...", file=sys.stderr)
                    return
            except Exception:
                traceback.print_exc()
            except BaseException:
                known.quit = True  # bypass the finally block below
                raise
            finally:
                if not known.quit:
                    input_ = shlex.split(input(f">>> {parser.prog} "))


def pretty_print(element: ET.Element) -> None:
    sans.indent(element)
    print(Syntax(ET.tostring(element, encoding="unicode").strip(), "xml"))


if __name__ == "__main__":
    sys.exit(main())
