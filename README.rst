sans
====

|pypi| |Code style: black| |Build Status| |Documentation Status| |Coverage Status|

Synchronous / Asynchronous NationStates (Python wrapper for the
NationStates API)

Installing
----------

::

   python3 -m pip install -U sans

Development version:

::

   python3 -m pip install -U https://github.com/zephyrkul/sans/archive/master.zip#egg=sans

Examples
--------

Asynchronous
~~~~~~~~~~~~

.. code:: py

   import asyncio
   import sans
   from lxml import etree

   async def main():
       sans.Api.agent = "Darcania"
       request = sans.Api(
           "fullname population flag census",
           nation="darcania",
           mode="score",
           scale="65 66",
       )
       root = await request
       pretty = root.to_pretty_string()
       print(pretty)

       request = sans.Dumps.REGIONS
       async for region in request:
           pretty = region.to_pretty_string()
           print(pretty)


   asyncio.run(main())  # Python 3.7+ only

Synchronous
~~~~~~~~~~~

.. code:: py

   import sans
   from lxml import etree

   def main():
       sans.run_in_thread()
       sans.Api.agent = "Darcania"
       request = sans.Api(
           "fullname population flag census",
           nation="darcania",
           mode="score",
           scale="65 66",
       )
       root = request.threadsafe()
       pretty = root.to_pretty_string()
       print(pretty)

       request = sans.Dumps.REGIONS
       for region in request.threadsafe:
           pretty = region.to_pretty_string()
           print(pretty)


   main()

Command Line
------------

::

   python3 -m sans --nation darcania census --scale "65 66" --mode score
   User Agent: Darcania
   <NATION>...</NATION>
   >>> --nation testlandia fullname
   <NATION>...</NATION>
   >>> --region "the north pacific" numnations lastupdate
   <REGION>...</REGION>
   >>>
   Exiting...

Requirements
------------

-  Python 3.6+
-  aiohttp
-  lxml

.. |pypi| image:: https://img.shields.io/pypi/v/sans.svg
   :target: https://pypi.python.org/pypi/sans
.. |Code style: black| image:: https://img.shields.io/badge/code%20style-black-000000.svg
   :target: https://github.com/ambv/black
.. |Build Status| image:: https://travis-ci.com/zephyrkul/sans.svg?branch=master
   :target: https://travis-ci.com/zephyrkul/sans
.. |Documentation Status| image:: https://readthedocs.org/projects/sans/badge/?version=latest
   :target: http://sans.readthedocs.org/en/latest/?badge=latest
.. |Coverage Status| image:: https://coveralls.io/repos/github/zephyrkul/sans/badge.svg?branch=master
   :target: https://coveralls.io/github/zephyrkul/sans?branch=master
