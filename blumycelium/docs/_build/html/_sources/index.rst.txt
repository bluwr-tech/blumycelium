.. Blumycellium documentation master file, created by
   sphinx-quickstart on Mon Mar  7 20:19:58 2022.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. image:: logo_full.png
  :width: 200
  :alt: BLUMYCELIUM

BLUMYCELIUM: Async micro-services, 100% in python from Bluwr
============================================================

PLEASE NOTE: This documentation is a work in progress

This tool os provided for free by bluwr.com_. We are building a 100% text based publication platform. A calm space free of any addictive feature.

Here are a few things that you can do to support us:
 - Register for early access on bluwr.com_.
 - Buy some awesoms merch on our store_
 - Follow us on social media: instagram_, twitter_, linkedin_

.. _bluwr.com: https://bluwr.com
.. _store: https://store.bluwr.com
.. _instagram: https://www.instagram.com/bluwr_official/
.. _twitter: https://twitter.com/bluwr_official
.. _linkedin: https://www.linkedin.com/company/bluwr


BLUMYCELIUM is our tool for arm's-length microservices management and orchestration. It allows for the splitting of a monolithic application into several small parts that run asynchronously in the same environment and can be tested separately. 

It was developed to be easy to learn and does not require more than python knowledge to achieve results that would normally be implemented using more complex DevOps orchestration tools mediated through REST APIs. To achieve this, Blumycellium relies heavily on python introspection capabilities to follow the flow of variable updates and transparently derives execution and orchestration graphs. By allowing services to be separate programs BLUMYCELIUM applications can also bypass the python GIL. BLUMYCELIUM also remembers the source code of all tasks as well as tracebacks for all exceptions for easy debugging. BLUMYCELIUM is implemented using the flexible multimodal ArangoDB database for storing what we call the: Mycelium. The repository of everything needed for variable execution graphs, source codes, orchestrations and failure reporting.

BLUMYCELIUM allows you to write complex microservice orchestration all in python. You can divide a complex application into many smaller parts that can be tested independtly and ran asynchronously. These smaller parts are agents called *Machine Elves* and the *Mycelium* is the database they use to communicate.

**Machine Elf <- Mycelium -> Machine Elf**

Arm's-length microservices?
---------------------------

Arm's-length microservices are microservices that trust each other completely. Only trusted elves should be allowed inside a mycelium. Myceliums are extremely convenient but not secure by default. It's you job to make sure that your myceliums are properly protected.


Glossary Mycelium?
------------------

**Machine Elf**: an indepedent agent that can perform a set of tasks. Elves can be processes or threads of the same application, or completely independant application hosted locally or remotely. 
**Task**: a function from a machine elf whose name starts with `task_`.
**Job**: a task to run.

**Mycelium**: a datastructure that stores many things related to the application like:
- Job orchestration
- Variable flows (how to compute values from python instructions)
- Elves documentation, source codes and revisions
- Tasks source code & documentation

For now the only mycelium implementation available uses the ArangoDB database and thus can be setup anywhere:
- locally
- on the cloud
- in a separate container
- inside the same container


Feedback
========

If you have any suggestions about features or feedback about the documentation please open github issues https://github.com/bluwr-tech/blumycelium.


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
   exceptions
   async

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`





