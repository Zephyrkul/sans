from __future__ import annotations

from datetime import date as _date
from typing import TYPE_CHECKING, Iterable, Mapping, NewType, overload

import httpx

if TYPE_CHECKING:
    from typing_extensions import Literal, TypeAlias

    _Shard = NewType("_Shard", dict[str, str])
    _QueryValueTypes: TypeAlias = "str | int | float | bool"

API_URL = httpx.URL("https://www.nationstates.net/cgi-bin/api.cgi")

__all__ = [
    "API_URL",
    "Nation",
    "Region",
    "World",
    "WA",
    "Command",
    "Shard",
    "View",
    "Range",
    "NationsDump",
    "RegionsDump",
    "CardsDump",
    "Telegram",
]


def _primitive_value_to_str(value: object) -> str:
    # match behavior with httpx
    if value is True:
        return "true"
    elif value is False:
        return "false"
    elif value is None:
        return ""
    return str(value)


def Nation(
    nation: str, *shards: str | _Shard, **parameters: _QueryValueTypes
) -> httpx.URL:
    return World(*shards, nation=nation, **parameters)


def Region(
    region: str, *shards: str | _Shard, **parameters: _QueryValueTypes
) -> httpx.URL:
    return World(*shards, region=region, **parameters)


def World(*shards: str | _Shard, **parameters: _QueryValueTypes) -> httpx.URL:
    q: list[_QueryValueTypes | None] = [parameters.pop("q", None)]
    query: dict[str, _QueryValueTypes] = {}
    for shard in shards:
        if isinstance(shard, Mapping):
            shard = dict(shard)
            q.append(shard.pop("q", None))
            query.update(shard.items())
        else:
            q.append(shard)
    q_str = " ".join(map(_primitive_value_to_str, filter(None, q)))
    if q_str:
        query["q"] = q_str
    query.update(parameters)
    return API_URL.copy_with(params=query)


def WA(
    wa: Literal[1, "1", 2, "2"], *shards: str | _Shard, **parameters: _QueryValueTypes
) -> httpx.URL:
    return World(*shards, wa=_primitive_value_to_str(wa), **parameters)


def Command(nation: str, c: str, **parameters: _QueryValueTypes) -> httpx.URL:
    return World(nation=nation, c=c, **parameters)


def Telegram(client: str, tgid: str, key: str, to: str) -> httpx.URL:
    return World(a="sendtg", client=client, tgid=tgid, key=key, to=to)


def Shard(q: str, **parameters: _QueryValueTypes) -> _Shard:
    parameters["q"] = q
    return parameters  # type: ignore


@overload
def View(*, nations: Iterable[str]) -> _Shard: ...
@overload
def View(*, regions: Iterable[str]) -> _Shard: ...


def View(*, nations: Iterable[str] = (), regions: Iterable[str] = ()) -> _Shard:
    if bool(nations) is bool(regions):
        raise TypeError("View requires exactly one of either nations or regions")
    if nations:
        nations = "nation:" + ",".join(
            (nations,) if isinstance(nations, str) else nations
        )
        return {"view": nations}  # type: ignore
    if regions:
        regions = "region:" + ",".join(
            (regions,) if isinstance(regions, str) else regions
        )
        return {"view": regions}  # type: ignore

    raise AssertionError("Unreachable code")


def Range(__from: str | int, __to: str | int) -> _Shard:
    return {
        "from": _primitive_value_to_str(__from),
        "to": _primitive_value_to_str(__to),
    }  # type: ignore


# https://www.nationstates.net/archive/nations/2018-09-30-nations-xml.gz
def NationsDump(date: _date | None = None) -> httpx.URL:
    if date:
        path = date.strftime("/archive/nations/%Y-%m-%d-nations-xml.gz")
    else:
        path = "/pages/nations.xml.gz"
    return API_URL.join(path)


# https://www.nationstates.net/archive/nations/2018-09-30-regions-xml.gz
def RegionsDump(date: _date | None = None) -> httpx.URL:
    if date:
        path = date.strftime("/archive/nations/%Y-%m-%d-regions-xml.gz")
    else:
        path = "/pages/regions.xml.gz"
    return API_URL.join(path)


def CardsDump(season: Literal[1, "1", 2, "2", 3, "3", 4, "4"]) -> httpx.URL:
    return API_URL.join(f"/pages/cardlist_S{season}.xml.gz")
