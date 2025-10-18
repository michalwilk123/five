# Local Claude Rules

## Coding Style Guidelines

- Prefer functional coding style over adding classes
- Functions should have the most simple input arguments and should return the most simple result
- Code can be redundant if it improves readability. Do not create code that is preemptively extensible
- Hard to understand code is the one that has a lot of logical constructs like if/forloops/try-except statements in close proximity to each other. Avoid writing hard to understand code. Try to split this logic into several functions
- Avoid default arguments for internal use functions. Call of internal functions should be as clear as possible
- Avoid None arguments. Try to clear out unknown arguments as early as possible
- Functions should be as pure as possible. Avoid side effects and mutable state if it is achievable
- Avoid global state
- Avoid local import statements and function definitions inside not always reachable code like if/def/try statements
- Avoid comments and docstrings. Code should be documentation itself
- Avoid issues with relative paths, do not use __file__

### Project Specific Rules
cli -> directory with only CLI - related logic. The command logic should reside in handlers.py file
core -> small functionality specific functions. Created for readability only. Not meant to be reusable. Common application specific functions should be in core/common.py
managers -> interfaces for other libraries / applications like git or sqllite. This will talk to external applications directly
utils.py -> universal logic not connected with the project itself

Only the managers can interface underline applications directly
The managers are used mainly by the core functions
cli directory does not contain the application logic

### Technical

Project uses uv to run it, pytest for testing. Other dependancies are click and ponyorm
