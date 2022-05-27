Code Design
===========

Here are some code design considerations when building a tool with blumycelium. 
Important to note that these are just suggestions, not restrictions. 
Your code will run even if you do it your own way.

Elf class parameter
-------------------

As you know by now, an elf's purpose is to execute tasks (python functions named `task_*`. Tasks functions take parameters, 
however, if some parameter is constant no matter what the task is, you might consider creating an Elf class containing a dedicated argument.
In that case we suggest implementing a separate constructor instead of using the default one.

The elf class instance will be created in 2 different places:

- When writing the orchestration code (saving the tasks in arangodb).
- When writing the code that will actually execute the tasks. 

In order to avoid parameter values sunchronization issues, hereunder is our code design suggestion. 

Suggestion :

  .. code-block:: python

    import blumycelium.machine_elf as melf

    class MyDummyElf(melf.MachineElf):

        def initialize(self, my_custom_parameter):
            self.my_custom_parameter = my_custom_parameter



Instead of:

  .. code-block:: python

    import blumycelium.machine_elf as melf

    class MyDummyElf(melf.MachineElf):

        def __init__(self, uid, mycelium, my_custom_parameter):
            self.my_custom_parameter = my_custom_parameter
            super().__init__(uid, mycelium)



