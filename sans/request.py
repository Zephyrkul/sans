from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING, Mapping

from httpx import URL, Request as RequestType

if TYPE_CHECKING:
    from typing_extensions import Literal
API_URL = URL("https://www.nationstates.net/cgi-bin/api.cgi")

__all__ = [
    "API_URL",
    "Request",
    "Nation",
    "Region",
    "World",
    "WA",
    "Shard",
    "NationsDump",
    "RegionsDump",
    "CardsDump",
]


def Request(*shards: str | Mapping[str, str], **parameters: str) -> RequestType:
    q: list[str | None] = [parameters.pop("q", None)]
    query: dict[str, str] = {}
    for shard in shards:
        try:
            shard = dict(shard)  # type: ignore
        except TypeError:
            q.append(str(shard))
        else:
            q.append(shard.pop("q", None))  # type: ignore
            query.update(shard)  # type: ignore
    query.update(parameters, q="+".join(map(str, filter(None, q))))
    if query.get("a", "").lower() == "sendtg":
        raise RuntimeError("sans does not currently support the telegram API.")
    return RequestType("GET", API_URL, params=query)


def Nation(nation: str, *shards: str, **parameters: str) -> RequestType:
    return Request(*shards, nation=nation, **parameters)


def Region(region: str, *shards: str, **parameters: str) -> RequestType:
    return Request(*shards, region=region, **parameters)


World = Request


def WA(wa: Literal[1, "1", 2, "2"], *shards: str, **parameters: str) -> RequestType:
    return Request(*shards, wa=str(wa), **parameters)


def Shard(q: str, **parameters: str) -> dict[str, str]:
    parameters["q"] = q
    return parameters


# https://www.nationstates.net/archive/nations/2018-09-30-nations-xml.gz
def NationsDump(date: date | None = None) -> RequestType:
    if date:
        path = date.strftime("/archive/nations/%Y-%m-%d-nations-xml.gz")
    else:
        path = "/pages/nations.xml.gz"
    return RequestType("GET", API_URL.join(path))


# https://www.nationstates.net/archive/nations/2018-09-30-regions-xml.gz
def RegionsDump(date: date | None = None) -> RequestType:
    if date:
        path = date.strftime("/archive/nations/%Y-%m-%d-regions-xml.gz")
    else:
        path = "/pages/regions.xml.gz"
    return RequestType("GET", API_URL.join(path))


def CardsDump(season: int):
    path = f"/pages/cardlist_S{season}.xml.gz"
    return RequestType("GET", API_URL.join(path))
