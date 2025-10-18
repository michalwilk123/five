# Synchronization Logic Design

## Overview

The synchronization module (`sync.py`) determines which commits are currently **applied** vs **reverted** in the Five system. This is essential for the checkout operation to understand the current state and what operations are needed.

## Core Assumption

**Five owns and controls the git repository.** Commits are never deleted or rebased. Once created, commits always exist in git. The only state change is whether a commit's changes are currently applied or have been reverted.

## Key Concepts

### SyncOperation Enum

Two possible states for each commit:

- **APPLIED**: Commit's changes are currently active in the repository
- **REVERTED**: Commit's changes have been undone (task has revert_commit_id set)

Uses `auto()` for enum values following best practices.

### Commit State

A commit is considered **REVERTED** when:
1. It's an assistant commit (has `completed_task_id`)
2. The associated task has a `revert_commit_id` set

All other commits are **APPLIED**.

## Core Functions

### `build_commit_state_map(db_manager: DatabaseManager) -> dict[int, bool]`

Builds a map of commit IDs to their applied state (True = applied, False = reverted).

**Logic**:
- Start by marking all commits as applied (True)
- For each assistant commit, check if its task has `revert_commit_id`
- If yes, mark that commit as reverted (False)

**Returns**: Dictionary mapping commit_id → is_applied

### `get_commits_up_to(db_manager: DatabaseManager, end_commit_id: int) -> list[dict]`

Retrieves all commits from database up to and including the specified commit ID.

**Parameters**:
- `end_commit_id`: Maximum commit ID to include

**Returns**: List of commit dictionaries filtered by ID

### `determine_operations(commits: list[dict], commit_state_map: dict[int, bool]) -> list[SyncOperation]`

Determines the sync operation needed for each commit based on the state map.

**Logic**:
- Look up each commit's ID in the state map
- If True → `SyncOperation.APPLIED`
- If False → `SyncOperation.REVERTED`

**Returns**: List of operations matching commits order

### `analyze_sync_state(db_manager: DatabaseManager, git_manager: GitManager, end_commit_id: int) -> tuple[list[dict], list[SyncOperation]]`

Main synchronization analysis function.

**Flow**:
1. Get all commits up to target
2. Build commit state map
3. Determine operations for each commit

**Returns**: Tuple of (commits, operations) where indices align

### Utility Functions

- `get_target_commit_hash(commits: list[dict], target_commit_id: int) -> str | None`
  - Finds the git hash for a specific commit ID
  - Returns None if commit not found

## GitManager Extensions

Added two new methods to GitManager:

### `get_all_commit_hashes() -> set[str]`

Retrieves all commit hashes from the git repository.

**Implementation**: `git log --all --format=%H`

**Returns**: Set of all commit hashes

### `get_current_head() -> str`

Gets the current HEAD commit hash.

**Implementation**: `git rev-parse HEAD`

**Returns**: Current HEAD hash

## Usage Example for Checkout

```python
from five_cli.core.sync import analyze_sync_state, SyncOperation

# Get task to checkout
task = db_manager.get_completed_task_entity_by_id(task_id)
assert task.revert_commit_id is None  # Task not cancelled

target_commit_id = task.commit_id

# Analyze state up to target commit
commits, operations = analyze_sync_state(db_manager, git_manager, target_commit_id)

# Process each commit
for commit, operation in zip(commits, operations):
    if operation == SyncOperation.APPLIED:
        # Commit is applied, no action needed
        pass
    elif operation == SyncOperation.REVERTED:
        # This commit was reverted, need to revert the revert
        # to make it visible again
        task = db_manager.get_completed_task_entity_by_id(commit['completed_task_id'])
        revert_commit = db_manager.get_commit_by_id(task.revert_commit_id)
        # Revert the revert commit to restore original changes
        git_manager.run(['revert', revert_commit['hash']])
```

## Design Decisions

### Functional Approach (Following CLAUDE.md)

- ✓ Pure functions with simple inputs/outputs
- ✓ No global state
- ✓ Clear function names that describe behavior
- ✓ Minimal comments - code is self-documenting
- ✓ No preemptive extensibility

### Single Responsibility

Each function has one clear job:

1. **State Building**: `build_commit_state_map()`
2. **Filtering**: `get_commits_up_to()`
3. **Mapping**: `determine_operations()`
4. **Orchestration**: `analyze_sync_state()`

### Manager-Based Git Operations

All git operations go through GitManager:
- No direct subprocess calls in sync.py
- Consistent logging and error handling
- Testable and mockable

### Correctness Over Performance

The state map is rebuilt on each analysis to ensure correctness. This is acceptable because:
- Checkout is not a frequent operation
- Commit count is typically small
- Correctness is more important than micro-optimizations

## Testing Strategy

Tests cover:
1. State map building (all applied)
2. State map building (with reverted commits)
3. Commit filtering by ID
4. Operation determination (all applied)
5. Operation determination (with reverted)
6. Full workflow (all applied)
7. Full workflow (with reverted commits)
8. Utility functions
9. GitManager extensions

All functions tested in isolation and as part of the complete workflow.

## Why This Design?

The key insight is that **Five never deletes git commits**. The sync problem is not about finding missing commits, but about determining which commits are currently "active" based on database state.

By tracking revert relationships in the database (`task.revert_commit_id`), we can accurately determine the current state without needing to parse git history or compare hashes.

This makes the sync logic:
- Simple and predictable
- Fast (no complex git operations)
- Reliable (single source of truth: the database)
