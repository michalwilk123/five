from pathlib import Path

from pony.orm import db_session, desc, exists, max, select

from five_cli.db_models import Commit, CompletedTask, Project, db
from five_cli.managers.base import BaseManager
from five_cli.utils import LogFunction


class DatabaseManager(BaseManager):
    def __init__(
        self,
        logger: LogFunction,
        db_path: Path,
    ):
        super().__init__(logger)
        self._db_path = db_path
        self._connected = False

    @property
    def db_path(self) -> Path:
        return self._db_path

    def connect(self, create_tables: bool):
        if db.provider:
            self._log(f'Database already bound to {db.provider.dialect}, disconnecting...')
            db.disconnect()
            db.provider = db.schema = None
            self._log('Database disconnected')

        self._log(f'Connecting to database at {self.db_path}')
        db.bind(provider='sqlite', filename=str(self.db_path), create_db=True)
        db.generate_mapping(create_tables=create_tables, check_tables=False)
        self._connected = True

    def get_latest_commit(self) -> Commit | None:
        return select(c for c in Commit).order_by(desc(Commit.id)).first()

    def get_next_commit_id(self) -> int:
        max_id = max(c.id for c in Commit) or 0
        return max_id + 1

    @db_session
    def create_project(
        self, name: str, path: str, git_repo_path: str | None, author: str | None
    ) -> Project:
        self._log(f'Creating project {name} at {path}')
        project_data = {'name': name, 'path': path}
        if git_repo_path is not None:
            project_data['git_repo_path'] = git_repo_path
        if author is not None:
            project_data['author'] = author
        return Project(**project_data)

    @db_session
    def get_project_by_path(self, path: str) -> Project | None:
        return Project.get(path=path)

    @db_session
    def get_all_project_names(self) -> list[str]:
        return select(p.name for p in Project)[:]

    @db_session
    def get_project_by_name(self, name: str) -> Project | None:
        return Project.get(name=name)

    @db_session
    def create_user_commit(self, commit_hash: str, note: str | None) -> Commit:
        self._log(f'Persisting user commit {commit_hash}')
        commit_data = {
            'hash': commit_hash,
            'type': 'user',
        }
        if note is not None:
            commit_data['note'] = note
        return Commit(**commit_data)

    def create_assistant_commit(
        self, commit_hash: str, completed_task_id: int, note: str | None
    ) -> Commit:
        self._log(f'Persisting assistant commit {commit_hash}')
        task = CompletedTask.get(id=completed_task_id)
        if task is None:
            raise ValueError(f'Completed task with ID {completed_task_id} not found')
        commit_data = {
            'hash': commit_hash,
            'type': 'assistant',
            'completed_task': task,
        }
        if note is not None:
            commit_data['note'] = note
        return Commit(**commit_data)

    def get_next_task_position(self) -> int:
        max_position = max(t.position for t in CompletedTask) or 0
        return max_position + 1

    def create_completed_task(
        self,
        commit_id: int,
        prompt: str,
        model_name: str | None,
        temperature: float | None,
        reference_ids: list[int],
        project: Project,
    ) -> CompletedTask:
        from five_cli.db_models import Reference

        position = self.get_next_task_position()
        task = CompletedTask(
            position=position,
            commit_id=commit_id,
            prompt=prompt,
            generated_code='',
            context='',
            model_name=model_name or '',
            temperature=temperature,
            project=project,
        )

        for ref_id in reference_ids:
            ref_task = CompletedTask.get(id=ref_id)
            if ref_task:
                Reference(task=task, referenced_task=ref_task)

        return task

    def get_commit_by_hash(self, commit_hash: str) -> Commit | None:
        return Commit.get(hash=commit_hash)

    def get_all_completed_tasks(self, project_id: int | None = None) -> list[dict]:
        if project_id is None:
            tasks = select(t for t in CompletedTask)[:]
        else:
            tasks = select(t for t in CompletedTask if t.project.id == project_id)[:]
        return [task.to_dict() for task in tasks]

    def get_completed_task_by_id(self, task_id: int) -> dict | None:
        task = CompletedTask.get(id=task_id)
        return task.to_dict() if task else None

    def get_commits_by_project_id(self, project_id: int | None) -> list[dict]:
        if project_id is None:
            commits = select(c for c in Commit)[:]
        else:
            commits = select(
                c
                for c in Commit
                if exists(
                    t
                    for t in CompletedTask
                    if t.project.id == project_id and (t.commit_id == c.id or c.completed_task is t)
                )
            )[:]
        return [commit.to_dict() for commit in commits]

    def get_commit_by_id(self, commit_id: int) -> dict | None:
        commit = Commit.get(id=commit_id)
        return commit.to_dict() if commit else None

    @db_session
    def get_all_projects(self) -> list[dict]:
        projects = select(p for p in Project)[:]
        return [project.to_dict() for project in projects]

    def get_project_by_id(self, project_id: int) -> dict | None:
        project = Project.get(id=project_id)
        return project.to_dict() if project else None

    def get_commit_entity_by_hash(self, commit_hash: str) -> Commit | None:
        return Commit.get(hash=commit_hash)

    def get_completed_task_entity_by_id(self, task_id: int) -> CompletedTask | None:
        return CompletedTask.get(id=task_id)

    def get_commit_entity_by_id(self, commit_id: int) -> Commit | None:
        return Commit.get(id=commit_id)

    @db_session
    def update_task_revert_commit_id(self, task_id: int, revert_commit_id: int):
        self._log(f'Updating task {task_id} with revert commit ID {revert_commit_id}')
        task = CompletedTask.get(id=task_id)
        if task:
            task.revert_commit_id = revert_commit_id
