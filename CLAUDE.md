# Coding Rules

## Core Principles

- Design functions with simple input arguments and simple return values.
- Write redundant code if it improves readability. Do not write preemptively extensible code.
- Write functional code. Do not create classes when functions suffice.

## Code Clarity

- Do not use default arguments for internal functions. Make all internal function calls explicit.
-Do not use None as an argument type. Resolve unknown arguments immediately.
- Split complex logic into multiple functions. Code becomes hard to understand when if statements, for loops, and try-except blocks appear in close proximity. Break these into separate functions.

## Validation and Safety

- Validate all inputs at the entry point. Fail fast.
- Write pure functions. Eliminate side effects and mutable state wherever possible.
- Do not use global state.

## Import and Structure Rules

- Place all imports at the top of the file. Do not use local imports or function definitions inside if statements, function definitions, or try blocks.
- Do not use relative paths. Do not reference `__file__`.
- Do not write comments or docstrings. The code is the documentation.

## Project Structure

**cli/** - Contains CLI logic only. Command implementation goes in `handlers.py`.
**core/** - Contains small, function-specific logic for readability. Not designed for reusability. Application-wide common functions go in `core/common.py`.
**managers/** - Interfaces for external libraries and applications (git, sqlite, etc.). Only managers communicate with external applications directly.
**utils.py** - Universal logic unrelated to the project domain.
**handlers.py** - implementation of the each command logic. Separated with UI
**validation.py** - validation logic

Managers interface with external applications. Core functions use managers. CLI directory does not contain application logic.

## Technical Stack

- **uv** for running the project
- **pytest** for testing
- **click** for CLI
- **ponyorm** for database