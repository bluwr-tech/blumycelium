BLUMYCELIUM: Async micro-services, 100% in python from Bluwr
============================================================

This tool os provided for free by [bluwr.com](https://bluwr.com). We are building a 100% text based publication platform. A calm space free of any addictive feature.

Here are a few things that you can do to support us:
 - Register for early access on [bluwr.com](https://bluwr.com)
 - Buy some awesoms merch on our [store](https://store.bluwr.com)
 - Follow us on social media [instagram](https://www.instagram.com/bluwr_official/), [twitter](https://twitter.com/bluwr_official), [linkedin](https://www.linkedin.com/company/bluwr)
 

**Machine Elf <- Mycelium -> Machine Elf**

PLEASE NOTE: This documentation is a work in progress

BLUMYCELIUM is our tool for arm's-length microservices management and orchestration. It allows for the splitting of a monolithic application into several small parts that run asynchronously in the same environment and can be tested separately. BLUMYCELIUM was developed to be easy to learn and does not require more than python knowledge to achieve results that would normally be implemented using more complex DevOps orchestration tools mediated through REST APIs. To achieve this, Blumycellium relies heavily on python introspection capabilities to follow the flow of variable updates and transparently derives execution and orchestration graphs. By allowing services to be separate programs BLUMYCELIUM applications can also bypass the python GIL. BLUMYCELIUM also remembers the source code of all tasks as well as tracebacks for all exceptions for easy debugging. BLUMYCELIUM is implemented using the flexible multimodal ArangoDB database for storing what we call the: Mycelium. The repository of everything needed for variable execution graphs, source codes, orchestrations and failure reporting.

BLUMYCELIUM allows you to write complex microservice orchestration all in python. You can divide a complex application into many smaller parts that can be tested independtly and ran asynchronously. These smaller parts are agents called *Machine Elves* and the *Mycelium* is the database they use to communicate.


 
Readthedocs documentation
=========================

We provide a full documentation [here](https://blumycelium.readthedocs.io/en/latest/index.html) (work in progress).


Feedback
========

If you have any suggestions about features or feedback about the documentation please open github issues.