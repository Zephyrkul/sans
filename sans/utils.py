from __future__ import annotations

import sys
from typing import Any, Coroutine, Mapping, overload
from xml.etree import ElementTree as etree

from .client import AsyncClientType, ClientType
from .response import Response
from .url import World

__all__ = ["prepare_and_execute", "indent"]


@overload
def prepare_and_execute(
    client: ClientType, *shards: str | Mapping[str, str], **parameters: str
) -> Response:
    ...


@overload
async def prepare_and_execute(
    client: AsyncClientType, *shards: str | Mapping[str, str], **parameters: str
) -> Response:
    ...


def prepare_and_execute(
    client: ClientType | AsyncClientType,
    *shards: str | Mapping[str, str],
    **parameters: str,
) -> Response | Coroutine[Any, Any, Response]:
    if isinstance(client, AsyncClientType):
        return _prepare_async(client, *shards, **parameters)
    request = World(*shards, **parameters, mode="prepare")
    response = client.get(request)
    response.raise_for_status()
    token: str = response.xml.find("SUCCESS").text  # type: ignore
    request = World(*shards, **parameters, mode="execute", token=token)
    return client.get(request)


async def _prepare_async(
    client: AsyncClientType, *shards: str | Mapping[str, str], **parameters: str
) -> Response:
    request = World(*shards, **parameters, mode="prepare")
    response = await client.get(request)
    response.raise_for_status()
    token: str = response.xml.find("SUCCESS").text  # type: ignore
    request = World(*shards, **parameters, mode="execute", token=token)
    return await client.get(request)


if sys.version_info < (3, 9):
    # from: https://github.com/python/cpython/blob/3.11/Lib/xml/etree/ElementTree.py#L1154
    def indent(
        tree: etree.Element | etree.ElementTree, space: str = "  ", level: int = 0
    ):
        if isinstance(tree, etree.ElementTree):
            tree = tree.getroot()
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
