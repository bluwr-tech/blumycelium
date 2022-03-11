Async demo
==========

(WIP)

Here are some details about the demo provided in `demos/daemons/`. 
The file async_orchestration.py is basically an asynchronous version of the demo in sync_orchestration.py. It starts 3 types of processes (elves):

- **Storage**: that represents an interface to a database that all elves connect to. It can be anything, here, for the sake of simplicity it is just a json file.
- **Animals**: that is an object that will be stored in the database (here the simple json file). It just contains the animal's species, and weight.
- **Stats**: that will compute some statistics using data stored in the database (again, just a json file here)

This example shows how these elves will run independently and their executions and dependencies will be all handled by bluycelium using Arangodb behind the scenes.





