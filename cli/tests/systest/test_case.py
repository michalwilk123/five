"""

Treat this code as an transaction. The test should come to initial state if it fails somewhere (like django transaction unit tests). Wrap everything in try/catch/finally: (DO IT HERE)
steps:
    
1) Go to tinydb repo and initialize five project using five project init

<- Check if repo is created, commit is added and if it is created by user (first commit should always be done by user)

2) Apply user-changes/change_1.patch

<- Repo should have unstaged changes. This should be visible in `five code status`

3) Run five project start-conversation

4) Apply user-changes/ai_changes.patch

5) Run five project stop-conversation Made up coversation data, make sure it reads/writes to the files

For the prompt use this (at least inspire yourself using this if you want)
I have a TinyDB project (a lightweight Python document database). I want you to add useful statistical and aggregation methods to the Table class to make data analysis easier for users.                                                 
                                                                                                                                                                                                                                             
  Please add the following methods to the Table class in tinydb/table.py:                                                                                                                                                                    
                                                                                                                                                                                                                                             
  1. sum(field, cond=None) - Calculate sum of numeric values in a field, with optional query condition                                                                                                                                       
  2. avg(field, cond=None) - Calculate average of numeric values in a field, with optional query condition                                                                                                                                   
  3. min(field, cond=None) - Find minimum value in a field, with optional query condition                                                                                                                                                    
  4. max(field, cond=None) - Find maximum value in a field, with optional query condition                                                                                                                                                    
  5. distinct(field, cond=None) - Get unique values in a field, with optional query condition                                                                                                                                                
                                                                                                                                                                                                                                             
  Requirements:                                                                                                                                                                                                                              
  - All methods should accept an optional cond parameter for filtering documents (like existing search and count methods)                                                                                                                    
  - Handle edge cases gracefully (empty results, non-existent fields, non-numeric values for sum/avg)
  - For sum/avg methods, raise ValueError if field contains non-numeric values
  - For distinct method, handle complex data types like lists and dicts properly
  - Follow the existing code style and patterns in the TinyDB codebase

  Also write comprehensive tests for all the new methods in tests/test_tinydb.py, including:
  - Basic functionality with and without conditions
  - Edge cases (empty database, non-existent fields, invalid data types)
  - Tests with complex data types for the distinct method

  Make sure all existing tests still pass after your changes.

a) When finished, this should create a commit (displayed using five code status). This commit should be created by assistant!
b) no changes should be unstaged

6) Apply user-changes/change_2.patch

7) five code status should show 2 commits (previous change_1.patch changes should be ammended to intial commit)

Check if the first commit has changes from change_1.patch

8) If the test pass or fail -> revert to initial state. Go to the tinydb directory and run this repo `cd tinydb && git stash && git reset --hard origin/master` the 

Something like:
    git add -A && git stash push -m "autostash-$(date +%s)" && git fetch origin && git reset --hard origin/master


"""
