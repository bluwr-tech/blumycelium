.. Blumycellium documentation master file, created by
   sphinx-quickstart on Mon Mar  7 20:19:58 2022.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

BLUMYCELIUM: Async micro-services, 100% in python from Bluwr
============================================================

PLEASE NOTE: This documentation is a work in progress

Blumycelium is our tool for arm's-length microservices management and orchestration. It allows for the splitting of a monolithic application into several small parts that run asynchronously in the same environment and can be tested separately. Blumycelium was developed to be fast and easy to learn and does not require more than python knowledge to achieve results that would normally be implemented using more complex DevOps orchestration tools mediated through REST APIs. To achieve this, Blumycellium relies heavily on python introspection capabilities to follow the flow of variable updates and transparently derives execution and orchestration graphs. By allowing services to be separate programs Blumycelium applications can also bypass the python GIL. Blumycelium also remembers the source code of all tasks as well as tracebacks for all exceptions for easy debugging. Blumycelium is implemented using the flexible multimodal ArangoDB database for storing what we call the: Mycelium. The repository of everything needed for variable execution graphs, source codes, orchestrations and failure reporting.


**Machine Elf <- Mycelium -> Machine Elf**

BLUMYCELIUM allows you to write complex microservice orchestration all in python. You can divide a complex application into many smaller parts that can be tested independtly and ran asynchronously. These smaller parts are agents called *Machine Elves* and the *Mycelium* is the database they use to communicate.

Myceliums are stored in an ArangoDB instance and can be setup anywhere you'd like:
	- Locally
	- On the cloud
	- Etc...
	

Arms-length microservices means that inside a mycelium we all trust each other, there are no credentials


.. toctree::
   :maxdepth: 2
   :caption: Contents:

   installation
   quickstart
   mycelium
   models
   graph_parameters
   machine_elf
   utils

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`





