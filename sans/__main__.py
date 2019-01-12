import aiohttp
import asyncio
import logging
import shlex
import sys
from lxml import etree

from .api import Api
from .utils import run_in_thread


logger = logging.getLogger(__name__)


def main():
    run_in_thread()
    Api.agent = input("User agent: ")
    args = None
    while True:
        if args is None:
            args = sys.argv[1:] or shlex.split(input(">>> "))
        else:
            args = shlex.split(input(">>> "))
        if not args:
            return print("Exiting...")
        request = {}
        key = "q"
        for arg in args:
            if arg.startswith("--"):
                key = arg[2:]
            else:
                request.setdefault(key, []).append(arg)
                key = "q"
        if key != "q":
            print("No value provided for key {!r}".format(key))
            continue
        request = Api(request)
        if not request:
            print("Bad Request")
            continue
        try:
            for element in request.threadsafe:
                print(element.to_pretty_string(), end="")
        except Exception as e:
            logging.exception(e)


if __name__ == "__main__":
    main()
