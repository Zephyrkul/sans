#!/usr/bin/python3

from __future__ import annotations

import argparse
import logging
import shlex
import sys
from contextlib import redirect_stdout
from getpass import getpass
from operator import methodcaller
from typing import TYPE_CHECKING, Any, Callable, NoReturn as Never
from xml.etree import ElementTree as ET

import sans

try:
    import readline  # noqa: F401
except ImportError:
    pass


def Syntax(arg: str, *_args: Any, **_kwargs: Any) -> object:
    return arg


if not TYPE_CHECKING:
    try:
        from rich import print
        from rich.console import Console
        from rich.logging import RichHandler
        from rich.syntax import Syntax  # noqa: F811
    except ImportError:
        logging.basicConfig(level=logging.ERROR)
    else:
        _console = Console(stderr=True)
        input = _console.input
        logging.basicConfig(
            level=logging.ERROR,
            handlers=[RichHandler(console=_console, rich_tracebacks=True)],
        )
        del _console

MAIN_LOG = logging.getLogger("sans.__main__")
SANS_LOG = logging.getLogger("sans")
ROOT_LOG = logging.getLogger()

SANS_LOG.setLevel(logging.WARNING)


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
                MAIN_LOG.exception(
                    "An exception occurred while handling your request:", exc_info=exc
                )
            try:
                with redirect_stdout(sys.stderr):
                    self.input = shlex.split(input(f"\n>>> {self.parser.prog} "))
                if not self.input:
                    sys.exit(0)
            except EOFError:
                sys.exit(0)
            return True
        return False


def main() -> Never:
    parser = argparse.ArgumentParser(
        description="SANS Console Entry",
        prog=sans.__name__,
        epilog="Any unknown args will be used to build the API request.",
    )
    parser.add_argument("--agent", "-A", help="set the script's user agent")
    parser.add_argument(
        "--auth",
        action="store_true",
        help="Prompt for a password for using private shards",
    )
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
        action="count",
        default=0,
        help="prints extra info about the request and response",
    )
    parser.add_argument(
        "--version", action="version", version=f"{parser.prog} {sans.__version__}"
    )
    reinput = _ReInput(parser)
    agent: str = ""
    auth = sans.NSAuth()  # type: ignore
    decoder: Callable[[bytes], str] = methodcaller(
        "decode", encoding=sys.stderr.encoding, errors="replace"
    )
    with sans.Client() as client:
        while True:
            with reinput as (known, unknown):
                level = max(
                    logging.DEBUG, logging.WARNING - logging.DEBUG * known.verbose
                )
                SANS_LOG.setLevel(level)
                ROOT_LOG.setLevel(level + logging.DEBUG)
                if known.auth:
                    auth.autologin = None
                    auth.password = getpass()
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
                            f"> {decoder(key)}: {decoder(value)}",
                            file=sys.stderr,
                        )
                    print(">", file=sys.stderr)
                response = client.send(request, auth=auth, stream=True)
                try:
                    if known.verbose:
                        print(
                            f"< HTTP/1.1 {response.status_code} {response.reason_phrase}",
                            file=sys.stderr,
                        )
                        for key, value in response.headers.raw:
                            print(
                                f"< {decoder(key)}: {decoder(value)}",
                                file=sys.stderr,
                            )
                        print("<", file=sys.stderr)
                    response.read()
                finally:
                    response.close()
                if response.content_type == "text/xml":
                    pretty_print(response.xml)
                elif response.content_type.startswith("text/"):
                    print(
                        Syntax(
                            response.text,
                            response.content_type.partition("/")[2],
                            background_color="default",
                            word_wrap=True,
                        )
                    )
                else:
                    print(response.content)
                if known.quit:
                    print("Exiting...", file=sys.stderr)
                    sys.exit(0)


def pretty_print(element: ET.Element, *, space: str = "  ") -> None:
    sans.indent(element, space)
    print(
        Syntax(
            ET.tostring(element, encoding="unicode").strip(),
            "xml",
            background_color="default",
            indent_guides=True,
            tab_size=len(space),
            word_wrap=True,
        )
    )


if __name__ == "__main__":
    logging.captureWarnings(True)
    sys.exit(main())
