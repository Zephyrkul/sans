from __future__ import annotations

import sys
from contextlib import ExitStack
from typing import Any, Coroutine, overload
from xml.etree import ElementTree as etree

import httpx

from .auth import NSAuth
from .client import AsyncClient, Client
from .errors import PrivateCommandError
from .response import Response
from .url import Command

__all__ = ["prepare_and_execute", "indent"]


@overload
def prepare_and_execute(
    client: Client | None, auth: NSAuth, nation: str, c: str, **parameters: str
) -> Response: ...


@overload
async def prepare_and_execute(
    client: AsyncClient, auth: NSAuth, nation: str, c: str, **parameters: str
) -> Response: ...


def prepare_and_execute(
    client: Client | AsyncClient | None,
    auth: NSAuth,
    nation: str,
    c: str,
    **parameters: str,
) -> Response | Coroutine[Any, Any, Response]:
    if isinstance(client, httpx.AsyncClient):
        return _prepare_async(client, auth, nation, c, **parameters)
    with ExitStack() as stack:
        if not client:
            client = stack.enter_context(Client())
        parameters.update(mode="prepare")
        url = Command(nation, c, **parameters)
        response = client.get(url, auth=auth)
        response.raise_for_status()
        error = response.xml.findtext("ERROR", default="")
        if error:
            raise PrivateCommandError(error, response=response)
        token = response.xml.findtext("SUCCESS", default="")
        parameters.update(mode="execute", token=token)
        url = Command(nation, c, **parameters, mode="execute", token=token)
        return client.get(url, auth=auth)


async def _prepare_async(
    client: AsyncClient, auth: NSAuth, nation: str, c: str, **parameters: str
) -> Response:
    parameters.update(mode="prepare")
    url = Command(nation, c, **parameters)
    response = await client.get(url, auth=auth)
    response.raise_for_status()
    error = response.xml.findtext("ERROR", default="")
    if error:
        raise PrivateCommandError(error, response=response)
    token = response.xml.findtext("SUCCESS", default="")
    parameters.update(mode="execute", token=token)
    url = Command(nation, c, **parameters)
    return await client.get(url, auth=auth)


if sys.version_info < (3, 9):
    # from: https://github.com/python/cpython/blob/3.11/Lib/xml/etree/ElementTree.py#L1154
    def indent(
        tree: etree.Element | etree.ElementTree, space: str = "  ", level: int = 0
    ):
        if isinstance(tree, etree.ElementTree):
            tree = tree.getroot()
        assert isinstance(tree, etree.Element)
        if level < 0:
            raise ValueError(f"Initial indentation level must be >= 0, got {level}")
        if not len(tree):
            return

        # Reduce the memory consumption by reusing indentation strings.
        indentations = ["\n" + level * space]

        def _indent_children(elem: etree.Element, level: int):
            # Start a new indentation level for the first child.
            child_level = level + 1
            try:
                child_indentation = indentations[child_level]
            except IndexError:
                child_indentation = indentations[level] + space
                indentations.append(child_indentation)

            if not elem.text or not elem.text.strip():
                elem.text = child_indentation

            for child in elem:
                if len(child):
                    _indent_children(child, child_level)
                if not child.tail or not child.tail.strip():
                    child.tail = child_indentation

            # Dedent after the last child by overwriting the previous indentation.
            if not child.tail.strip():  # type: ignore
                child.tail = indentations[level]  # type: ignore

        _indent_children(tree, 0)

else:
    from xml.etree.ElementTree import indent
