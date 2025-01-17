# sans

[![pypi](https://img.shields.io/pypi/v/sans.svg)](https://pypi.org/project/sans/)
[![Licensed under the MIT License](https://img.shields.io/pypi/l/sans.svg)](https://choosealicense.com/licenses/mit/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/Zephyrkul/sans/master.svg)](https://results.pre-commit.ci/latest/github/Zephyrkul/sans/master)
[![Documentation Status](https://readthedocs.org/projects/sans/badge/?version=latest)](http://sans.readthedocs.org/en/latest/?badge=latest)

**S**ynchronous / **A**synchronous **N**ation**S**tates

A [fully typed](https://docs.python.org/3/library/typing.html) extension for [HTTPX](https://www.python-httpx.org/) for the [NationStates API](https://www.nationstates.net/pages/api.html).

## Installing

```sh
python3 -m pip install -U sans
```

Development version:

```sh
python3 -m pip install -U https://github.com/zephyrkul/sans/archive/master.zip#egg=sans
```

## Support

If you need help with using sans, find a bug, or have a feature request, feel free to find me in the [NS Coders](https://discord.gg/SgwWMTN) Discord server, or [file an issue](https://github.com/Zephyrkul/sans/issues/new/choose).

## Examples

### Synchronous

```py
import sans
from xml.etree import ElementTree as ET

def main():
   sans.set_agent("Darcania")
   request = sans.Nation(
      "darcania",
      "fullname population flag census",
      mode="score",
      scale="65 66",
   )
   root = sans.get(request).xml
   sans.indent(root)
   print(ET.tostring(root, encoding="unicode"))

   with sans.stream("GET", sans.RegionsDump()) as response:
      for region in response.iter_xml():
         sans.indent(region)
         print(ET.tostring(region, encoding="unicode"))

if __name__ == "__main__":
   main()
```

### Asynchronous

```py
import asyncio
import sans
from xml.etree import ElementTree as ET

async def main():
   sans.set_agent("Darcania")
   async with sans.AsyncClient() as client:
      request = sans.Nation(
         "darcania",
         "fullname population flag census",
         mode="score",
         scale="65 66",
      )
      root = (await client.get(request)).xml
      sans.indent(root)
      print(ET.tostring(root, encoding="unicode"))

      async with client.stream("GET", sans.RegionsDump()) as response:
         async for region in response.aiter_xml():
            sans.indent(region)
            print(ET.tostring(region, encoding="unicode"))

if __name__ == "__main__":
   asyncio.run(main())
```

### Authentication

```py
auth = sans.NSAuth(password="hunter2")
sans.get(sans.Nation("testlandia", "ping"), auth=auth)
# X-Autologin is automatically retrieved and stored for when the auth object is re-used
print(auth.autologin)
# X-Pin is cached internally for repeated requests
root = sans.get(sans.Nation("testlandia", "packs"), auth=auth).xml
```

### Telegrams

```py
limiter = sans.TelegramLimiter(recruitment=False)
# The Telegram API can be used without a TelegramLimiter, but marking it ahead of time can save an API call.
response = sans.get(sans.Telegram(client="abcd1234", tgid="1234", key="abcdef1234567890", to="testlandia"), auth=limiter)
assert response.content == b"queued"
```

### Server-Sent Events

```py
for event in sans.serversent_events(
   client, "move", "founding", "cte", "member", "endo"
).view(regions=["the north pacific"]):
   print(event["str"])
```

## Command Line

```xml
sans --nation darcania census --scale "65 66" --mode score --agent Darcania
<NATION id="darcania">
   <CENSUS>
      <SCALE id="65">
         <SCORE>8145.00</SCORE>
      </SCALE>
      <SCALE id="66">
         <SCORE>0.00</SCORE>
      </SCALE>
   </CENSUS>
</NATION>

sans --nation testlandia fullname
<NATION id="testlandia">
   <FULLNAME>The Hive Mind of Testlandia</FULLNAME>
</NATION>

sans --region "the north pacific" numnations lastupdate
<REGION id="the_north_pacific">
   <LASTUPDATE>1685681810</LASTUPDATE>
   <NUMNATIONS>9535</NUMNATIONS>
</REGION>

sans --quit
No query provided. Exiting...
```

## Requirements

- [Python 3.7+](https://www.python.org/)
- [httpx](https://pypi.org/project/httpx/)
