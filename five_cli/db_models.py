from datetime import datetime

from pony.orm import Database, Optional, PrimaryKey, Required, Set

db = Database()

class CompletedTask(db.Entity):
    id = PrimaryKey(int, auto=True)
    position = Required(int, unique=True, sql_default='0')
    commit_id = Optional(int)
    prompt = Required(str)
    generated_code = Optional(str, default='')
    context = Optional(str, default='')
    model_name = Optional(str, default='')
    temperature = Optional(float)
    timestamp = Required(datetime, default=lambda: datetime.now())
    revert_commit_id = Optional(int)
    project = Required('Project')
    references = Set('Reference', reverse='task')
    referenced_by = Set('Reference', reverse='referenced_task')

    def is_deleted(self) -> bool:
        return self.revert_commit_id is not None

    def to_dict(self):
        return {
            'id': self.id,
            'position': self.position,
            'commit_id': self.commit_id,
            'prompt': self.prompt,
            'generated_code': self.generated_code,
            'context': self.context,
            'model_name': self.model_name,
            'temperature': self.temperature,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'revert_commit_id': self.revert_commit_id,
            'project_id': self.project.id if self.project else None,
        }


class Reference(db.Entity):
    task = Required('CompletedTask')
    referenced_task = Required('CompletedTask')


class Commit(db.Entity):
    id = PrimaryKey(int, auto=True)
    hash = Required(str, unique=True)
    type = Required(str)
    timestamp = Required(datetime, default=lambda: datetime.now())
    note = Optional(str)
    completed_task_id = Optional(int)

    def to_dict(self):
        return {
            'id': self.id,
            'hash': self.hash,
            'type': self.type,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'note': self.note,
            'completed_task_id': self.completed_task_id,
        }


class Project(db.Entity):
    id = PrimaryKey(int, auto=True)
    name = Required(str, unique=True)
    path = Required(str)
    git_repo_path = Optional(str)
    author = Optional(str)
    timestamp = Required(datetime, default=lambda: datetime.now())
    tasks = Set('CompletedTask')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'path': self.path,
            'git_repo_path': self.git_repo_path,
            'author': self.author,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
        }