from __future__ import annotations

import sys
from typing import Any, Coroutine, Mapping, overload
from xml.etree import ElementTree as etree

from .client import AsyncClientType, ClientType
from .request import Request
from .response import Response

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
    request = Request(*shards, **parameters, mode="prepare")
    response = client.send(request)
    token: str = response.xml.find("TOKEN").text  # type: ignore
    request = Request(*shards, **parameters, mode="execute", token=token)
    return client.send(request)


async def _prepare_async(
    client: AsyncClientType, *shards: str | Mapping[str, str], **parameters: str
) -> Response:
    request = Request(*shards, **parameters, mode="prepare")
    response = await client.send(request)
    token: str = response.xml.find("TOKEN").text  # type: ignore
    request = Request(*shards, **parameters, mode="execute", token=token)
    return await client.send(request)


if sys.version_info < (3, 9):

    def indent(
        tree: etree.Element | etree.ElementTree,
        space: str = "  ",
        level: int = 0,
        *,
        _parent: etree.Element | None = None,
        _index: int = -1,
    ) -> None:
        """Backport of ElementTree.indent"""
        if not _parent and isinstance(tree, etree.ElementTree):
            tree = tree.getroot()
        assert isinstance(tree, etree.Element)
        for i, node in enumerate(tree):
            indent(node, space, level + 1, _parent=tree, _index=i)
        if _parent is not None:
            if _index == 0:
                _parent.text = "\n" + (space * level)
            else:
                _parent[_index - 1].tail = "\n" + (space * level)
            if _index == len(_parent) - 1:
                tree.tail = "\n" + (space * (level - 1))

else:
    from xml.etree.ElementTree import indent
