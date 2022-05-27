Limits
=======

Tasks paramters
---------------

Elves execute tasks which are simply python function. These functions can take argument which have to be stored in Arangodb for later execution.
Only a few restrictions apply to task parameters. 

Allowed:

- Numbers (integers, floats etc.)
- Strings
- Booleans
- lists

They can't be:

- Objects
- Functions
- Dictionnaries

For lists for now make sure they are not too big. Starting ~100,000 elements, the way we store them in Arangodb can cause performance issues.
Check the corresponding issue to see where we are at https://github.com/bluwr-tech/blumycelium/issues/5.

