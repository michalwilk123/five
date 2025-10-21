
## Test systemowy five:
Init działa. Poprawnie pyta o pliki systemowe. Wygląda jakby poprawnie tworzył tabele i plik <project-name>
track start i track stop działaja
pozostaja edge casy:
- track start przy zmienionych plikach
- track cancel + zmiana plikow ponowna (powinno stworzyc kolejnego user commita

five undo WORKS
five redo WORKS

five get commits powinno pokazywac rowniez user commity OK


2) Dodanie nowego projektu
powtorzenie gornych testow i sprawdzenie czy dzialaja cały czas


### Problems
1) Issue: The `project` attribute (default value does not work)

michal@michal-machine5:~/Programming/test/five-systest$ five get completed-tasks
Usage: five get completed-tasks [OPTIONS] [TASK_ID]
Try 'five get completed-tasks --help' for help.
Error: Invalid value for '--config': Cannot resolve project config without both --project and --global-config.

It is the same issue for `five track` commands:

michal@michal-machine5:~/Programming/test/five-systest$ five track start
Usage: five track start [OPTIONS]
Try 'five track start --help' for help.

Error: Invalid value for '--config': Cannot resolve project config without both --project and --global-config.

if user inputs `five track start`, it should assume the project path is current path

Currently it throws :
  File "/home/michal/.local/lib/python3.12/site-packages/five/cli/decorators.py", line 41, in _validate_project_config_path
    project_path: Path | None = ctx.params['project']
                                ~~~~~~~~~~^^^^^^^^^^^
KeyError: 'project'

So it means that the global config path and project path are in wrong order


2) Add short documentation to commands get init setup it is currently very poor

3) five track cancel has poor docs

4) `five get completed-tasks` returns wrong output

Example:
[{"id": 1, "position": 1, "commit_id": 1, "prompt": "create me simple hangman game in python cli. Use standard library and keep code below 100 lines", "generated_code": "", "context": "", "model_name": "", "temperature": null, "timestamp": "2025-10-21T19:01:28.503625", "revert_commit_id": null, "project_id": 1}]

List view:
There should be no "generated_code" entry in output at all

Detail:
In detail view the command `five get completed-tasks` should in generated_code display the output of 
`git diff` command. The git commit hash you can easily get from Commit table

In the same manner the `five get commits` command should work

detail view should add additional "diff" field which would display the diff

5) `five get project` should be -> `five get projects` to match other functions in file @five/cli/get.py


6) `five track stop` -> there should be optional parameter "note" that would be just some user note. This field is already used in database schema @five/db_models.py in model Commit and there is no way to populate it
Please add a way to fill that field

7) Please create `five track status`
Which would just check if the state file exists. This command should be very similar to `five track cancel`

8) Please create alias for common commands:
five track stop -> add five track end


