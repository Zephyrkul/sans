sans
====

|pypi| |Code style: black| |Build Status| |Documentation Status|

**S**\ ynchronous / **A**\ synchronous **N**\ ation\ **S**\ tates

An extension for `HTTPX <https://www.python-httpx.org/>`_ for the `NationStates API <https://www.nationstates.net/pages/api.html>`_

Installing
----------

.. code::

   python3 -m pip install -U sans

Development version:

.. code::

   python3 -m pip install -U https://github.com/zephyrkul/sans/archive/master.zip#egg=sans

Examples
--------

Synchronous
~~~~~~~~~~~

.. code:: python

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
      root = sans.get(request)
      sans.indent(root)
      print(ET.tostring(root, encoding="unicode"))

      with sans.stream("GET", sans.RegionsDump()) as response:
         for region in response.iter_xml():
            sans.indent(region)
            print(ET.tostring(region, encoding="unicode"))

   if __name__ == "__main__":
      main()

Asynchronous
~~~~~~~~~~~~

.. code:: python

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
         root = (await client.send(request)).xml
         sans.indent(root)
         print(ET.tostring(root, encoding="unicode"))

         async with client.stream("GET", sans.RegionsDump()) as response:
            async for region in response.aiter_xml():
               sans.indent(region)
               print(ET.tostring(region, encoding="unicode"))

   if __name__ == "__main__":
      asyncio.run(main())

Command Line
------------

.. code::

   $ sans --nation darcania census --scale "65 66" --mode score --agent Darcania

   <CENSUS>
      <SCALE id="65">
         <SCORE>4949.00</SCORE>
      </SCALE>
      <SCALE id="66">
         <SCORE>130.00</SCORE>
      </SCALE>
   </CENSUS>

   $ sans --nation testlandia fullname

   <FULLNAME>The Hive Mind of Testlandia</FULLNAME>

   sans --region "the north pacific" numnations lastupdate

   <LASTUPDATE>1683650325</LASTUPDATE>
   <NUMNATIONS>10503</NUMNATIONS>

   $ sans --quit
   No query provided. Exiting...

Requirements
------------

-  Python 3.7+
-  httpx

.. |pypi| image:: https://img.shields.io/pypi/v/sans.svg
   :target: https://pypi.python.org/pypi/sans
   :alt: pypi version
.. |Code style: black| image:: https://img.shields.io/badge/code%20style-black-000000.svg
   :target: https://github.com/ambv/black
.. |Build Status| image:: https://results.pre-commit.ci/badge/github/Zephyrkul/sans/master.svg
   :target: https://results.pre-commit.ci/latest/github/Zephyrkul/sans/master
   :alt: pre-commit.ci status
.. |Documentation Status| image:: https://readthedocs.org/projects/sans/badge/?version=latest
   :target: http://sans.readthedocs.org/en/latest/?badge=latest
