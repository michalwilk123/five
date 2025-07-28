"""Documentation for indexer CLI commands."""

CREATE_HELP = """Create a new code index for a project.

This command scans the project directory and builds an index of all code symbols
(functions, classes, variables) found in the project files. The index is saved
to a .five directory in the project root.

Examples:
  # Create index for current directory
  indexer create

  # Create index for specific project with progress
  indexer create --project /path/to/project --progress

  # Create index for JavaScript project
  indexer create --language javascript
"""

UPDATE_HELP = """Update an existing code index.

This command checks for changes in the project files and updates the index
accordingly. It only processes files that have been modified, added, or deleted
since the last index update.

Examples:
  # Update index for current directory
  indexer update

  # Check what would change without updating
  indexer update --dry-run

  # Update with progress indication
  indexer update --progress
"""

SEARCH_HELP = """Search for symbols in the code index.

This command searches through the indexed symbols to find matches based on
your query. It supports both interactive and non-interactive modes.

Examples:
  # Interactive search
  indexer search

  # Search for specific function
  indexer search --query "get_user" --no-interactive

  # Search with code preview
  indexer search --query "class" --show-code --no-interactive

  # Search with custom result limit
  indexer search --max-results 100 --query "test"
"""

FOLD_HELP = """Fold code in a file based on the index.

This command displays a folded view of a file, showing only the structural
elements (classes, functions) at different levels of detail.

FILE_SPEC: File path with optional line range (e.g., file.py:20-400)
LEVEL: Folding level (0-3, default: 1)
  - 0: Only top-level classes
  - 1: Classes and global functions
  - 2: Classes, functions, and methods
  - 3: Show everything (no folding)

Examples:
  # Fold entire file at level 1
  indexer fold src/main.py

  # Fold specific range with line numbers
  indexer fold src/main.py:10-50 --numbers

  # Fold at different levels
  indexer fold src/main.py 0  # Only classes
  indexer fold src/main.py 2  # Classes, functions, methods
"""

EDIT_HELP = """Apply diff operations to files in the project.

This command reads diff operations from stdin and applies them to files in the
project. It supports replacing lines in files with new content.

Diff Format:
  Each diff operation consists of:
  1. Header line: ======filepath:start_line+end_line
  2. Content lines: The new content to replace the specified lines
  3. End marker: ======end

  Multiple operations can be specified, one after another.

Examples:
  # Apply diff from file
  cat changes.diff | indexer edit --project /path/to/project

  # Apply diff from command output
  echo "======src/main.py:10+12
  new line 1
  new line 2
  ======end" | indexer edit

  # Replace multiple lines in different files
  echo "======src/file1.py:5+5
  replacement line
  ======end
  ======src/file2.py:10+12
  line 1
  line 2
  line 3
  ======end" | indexer edit

Notes:
  - Line numbers are 1-indexed
  - Operations are applied in reverse order (highest line numbers first)
  - Overlapping line ranges are not allowed
  - Files must exist and not be empty
  - All operations must be valid before any are applied
"""
