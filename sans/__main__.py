#!/usr/bin/python3

from __future__ import annotations

import argparse
import logging
import shlex
import sys
from contextlib import redirect_stdout
from operator import methodcaller
from typing import TYPE_CHECKING, Any, Callable, NoReturn as Never
from xml.etree import ElementTree as ET

import sans

try:
    import readline  # noqa: F401
except ImportError:
    pass


if TYPE_CHECKING:

    def Syntax(arg: str, *_args: Any, **_kwargs: Any) -> object:
        return arg

else:
    try:
        from rich import print
        from rich.syntax import Syntax
        from rich.traceback import install
    except ImportError:
        pass
    else:
        install()
        del install


class _ReInput:
    def __init__(self, parser: argparse.ArgumentParser) -> None:
        self.parser = parser
        self.input: list[str] | None = None

    def __enter__(self):
        return self.parser.parse_known_args(self.input)

    def __exit__(self, *exc_details):
        exc: BaseException | None = exc_details[1]
        if exc is None or isinstance(exc, Exception):
            if exc is not None:
                sys.excepthook(type(exc), exc, exc.__traceback__)
            try:
                with redirect_stdout(sys.stderr):
                    self.input = shlex.split(input(f"\n>>> {sans.__name__} "))
            except EOFError:
                sys.exit(0)
            return True
        return False


def main() -> Never:
    parser = argparse.ArgumentParser(
        allow_abbrev=False,
        description="SANS Console Entry",
        prog=sans.__name__,
        epilog="Any unknown args will be used to build the API request.",
    )
    parser.add_argument("--agent", "-A", help="set the script's user agent")
    parser.add_argument(
        "--quit",
        "--exit",
        action="store_true",
        help="quit the console program loop after this run",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        "--url",
        "--headers",
        action="store_true",
        help="prints extra info about the request and response",
    )
    parser.add_argument("--version", action="version", version=sans.__version__)
    reinput = _ReInput(parser)
    agent: str = ""
    decoder: Callable[[bytes], str] = methodcaller(
        "decode", encoding=sys.stderr.encoding, errors="replace"
    )
    with sans.Client() as client:
        while True:
            with reinput as (known, unknown):
                if known.agent:
                    try:
                        agent = sans.set_agent(known.agent)
                        print(f"Agent set: {agent}", file=sys.stderr)
                    except RuntimeError:
                        print(
                            "You can't change the agent in the middle of the script.",
                            file=sys.stderr,
                        )
                if not unknown:
                    if known.quit:
                        print("No query provided. Exiting...", file=sys.stderr)
                        sys.exit(0)
                    print("No query provided.", file=sys.stderr)
                    if not any(vars(known).values()):
                        parser.print_help(sys.stderr)
                    continue
                parameters: dict[str, list[str]] = {}
                key = "q"
                for arg in unknown:
                    if arg.startswith("--"):
                        if key != "q":
                            print(
                                f"No value provided for key {key!r}",
                                file=sys.stderr,
                            )
                        key = arg[2:]
                    else:
                        parameters.setdefault(key, []).append(arg)
                        key = "q"
                if key != "q":
                    print(f"No value provided for key {key!r}", file=sys.stderr)
                request = client.build_request(
                    "GET",
                    sans.World(**{k: " ".join(v) for k, v in parameters.items()}),
                    headers={"User-Agent": agent},
                )
                if known.verbose:
                    print(
                        f"> {request.method} {decoder(request.url.raw_path)} HTTP/1.1",
                        file=sys.stderr,
                    )
                    for key, value in request.headers.raw:
                        print(
                            f"> {decoder(key).title()}: {decoder(value)}",
                            file=sys.stderr,
                        )
                    print(">", file=sys.stderr)
                response = client.send(request)
                if known.verbose:
                    print(
                        f"< HTTP/1.1 {response.status_code} {response.reason_phrase}",
                        file=sys.stderr,
                    )
                    for key, value in response.headers.raw:
                        print(
                            f"< {decoder(key).title()}: {decoder(value)}",
                            file=sys.stderr,
                        )
                    print("<", file=sys.stderr)
                if response.content_type == "text/xml":
                    pretty_print(response.xml)
                elif response.content_type == "text/plain":
                    print(response.text)
                else:
                    print(response.content)
                if known.quit:
                    print("Exiting...", file=sys.stderr)
                    sys.exit(0)


def pretty_print(element: ET.Element) -> None:
    sans.indent(element)
    print(Syntax(ET.tostring(element, encoding="unicode").strip(), "xml"))


if __name__ == "__main__":
    logging.captureWarnings(True)
    sys.exit(main())
