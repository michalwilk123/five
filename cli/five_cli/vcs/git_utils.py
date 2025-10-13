import os
import subprocess
from contextlib import contextmanager

FIVE_GITIGNORE_SEPARATOR = '\n' + '#' * 80 + '\n# Five-specific ignore rules\n' + '#' * 80


class GitRepo:
    def __init__(self, git_dir: str, work_tree: str):
        self.git_dir = git_dir
        self.work_tree = work_tree

    def run(self, args: list[str]) -> subprocess.CompletedProcess:
        cmd = ['git', '--git-dir', self.git_dir, '--work-tree', self.work_tree]
        cmd.extend(args)
        try:
            return subprocess.run(cmd, capture_output=True, check=True, text=True)
        except subprocess.CalledProcessError as e:
            error_msg = f"Git command failed: {' '.join(cmd)}\nstdout: {e.stdout}\nstderr: {e.stderr}"
            raise subprocess.CalledProcessError(e.returncode, e.cmd, e.stdout, e.stderr) from Exception(error_msg)

    @contextmanager
    def my_rebase(self, **kwargs):
        pass

    def test_rebase(self):

        with self.my_rebase(strategy="ours") as f:
            f.replace("123", "")

            f.run()

        self.run_rebase(
            replace_string="abc",
            target="somehash",
            on_conflict="",
        )

        pass

    @contextmanager
    def stage_and_commit(self, message: str, amend: bool = False):
        yield
        self.run(['add', '-A'])
        commit_args = ['commit', '-m', message]
        if amend:
            commit_args.insert(1, '--amend')
        self.run(commit_args)

    def get_status(self):
        status_result = self.run(['status', '--porcelain'])
        lines = status_result.stdout.strip().split('\n') if status_result.stdout.strip() else []

        untracked_files = []
        modified_files = []
        staged_files = []

        for line in lines:
            if len(line) < 3:
                continue

            status_code = line[:2]
            file_path = line[2:].lstrip()

            if status_code[0] != ' ' and status_code[0] != '?':
                staged_files.append(file_path)
            if status_code[1] != ' ':
                modified_files.append(file_path)
            if status_code == '??':
                untracked_files.append(file_path)

        is_dirty = len(lines) > 0

        return {
            'untracked_files': untracked_files,
            'modified_files': modified_files,
            'staged_files': staged_files,
            'is_dirty': is_dirty,
        }

    def get_last_commit_message(self):
        result = self.run(['log', '-1', '--format=%s'])
        return result.stdout.strip()

    def amend_last_commit(self, message: str):
        self.run(['add', '-A'])
        self.run(['commit', '--amend', '-m', message])

    def create_commit(self, message: str):
        with self.stage_and_commit(message):
            pass
        commit_hash_result = self.run(['rev-parse', 'HEAD'])
        return commit_hash_result.stdout.strip()

    def get_log(self, max_count: int):
        commits = []
        result = self.run([
            'log',
            '--format=%H|%an|%ad|%s',
            '--date=iso',
            f'-{max_count}',
        ])

        for line in result.stdout.split('\n'):
            if not line.strip():
                continue

            parts = line.split('|', 3)
            if len(parts) < 4:
                continue

            commit_hash, author, date_str, message = parts

            date_parts = date_str.split(' ')
            formatted_date = f'{date_parts[0]} {date_parts[1]}' if len(date_parts) >= 2 else date_str

            commit_info = {
                'hash': commit_hash[:8],
                'full_hash': commit_hash,
                'message': message.strip(),
                'timestamp': date_str,
                'author': author,
                'date': formatted_date,
            }

            commits.append(commit_info)

        return commits

    def get_detailed_changes(self):
        changes = []
        status_lines = self._get_status_lines()

        for line in status_lines:
            parsed = self._parse_porcelain_status_line(line)
            if not parsed:
                continue

            status_code, file_path = parsed

            if status_code == '??':
                changes.append({'file': file_path, 'status': 'untracked', 'additions': 0, 'deletions': 0})
                continue

            additions, deletions = self._get_file_diff_stats(file_path)
            file_status = self._decode_file_status(status_code)

            changes.append({
                'file': file_path,
                'status': file_status,
                'additions': additions,
                'deletions': deletions,
            })

        return changes

    def find_commit_by_message_match(self, predicate):
        """Find a commit where the message matches the given predicate function.

        Args:
            predicate: A function that takes a commit message string and returns True if it matches

        Returns:
            The commit hash if found, None otherwise
        """
        result = self.run(['log', '--format=%H|%s', '--all'])

        for line in result.stdout.split('\n'):
            if not line.strip():
                continue

            parts = line.split('|', 1)
            if len(parts) < 2:
                continue

            commit_hash, message = parts
            if predicate(message.strip()):
                return commit_hash.strip()

        return None

    def get_commit_diff(self, commit_hash: str):
        result = self.run(['show', '--format=', commit_hash])
        return result.stdout

    def reset_working_tree_changes(self):
        self.run(['reset', '--hard', 'HEAD'])
        self.run(['clean', '-fd'])

    def is_rebase_in_progress(self):
        rebase_merge_dir = os.path.join(self.git_dir, 'rebase-merge')
        rebase_apply_dir = os.path.join(self.git_dir, 'rebase-apply')
        return os.path.exists(rebase_merge_dir) or os.path.exists(rebase_apply_dir)

    def abort_rebase(self):
        try:
            self.run(['rebase', '--abort'])
        except subprocess.CalledProcessError:
            pass

    def continue_rebase(self):
        self.run(['rebase', '--continue'])

    @contextmanager
    def interactive_rebase(self, parent_hash: str, sed_command: str, auto_continue: bool = True):
        env = os.environ.copy()
        env['GIT_SEQUENCE_EDITOR'] = f"sed -i '{sed_command}'"

        cmd = ['git', '--git-dir', self.git_dir, '--work-tree', self.work_tree,
               'rebase', '-i', '-X', 'theirs', parent_hash]
        result = subprocess.run(cmd, capture_output=True, text=True, env=env)

        if result.returncode != 0:
            self.abort_rebase()
            raise RuntimeError(f'Rebase failed: {result.stderr}')

        try:
            yield
            if auto_continue and self.is_rebase_in_progress():
                self.continue_rebase()
        except Exception:
            if self.is_rebase_in_progress():
                self.abort_rebase()
            raise

    def get_commit_parent(self, commit_hash: str) -> str:
        """Get the parent of a commit. Returns the parent hash or raises an error."""
        try:
            # Try using ~1 notation first (more reliable)
            result = self.run(['rev-parse', f'{commit_hash}~1'])
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            # Fallback to ^ notation
            try:
                result = self.run(['rev-parse', f'{commit_hash}^'])
                return result.stdout.strip()
            except subprocess.CalledProcessError as e:
                raise ValueError(f"Commit {commit_hash} has no parent (might be root commit)") from e

    def rebase_drop_commit(self, commit_hash: str):
        parent_hash = self.get_commit_parent(commit_hash)
        sed_command = f's/^pick {commit_hash[:7]}/drop {commit_hash[:7]}/'
        with self.interactive_rebase(parent_hash, sed_command, auto_continue=True):
            pass

    def rebase_edit_commit(self, commit_hash: str):
        parent_hash = self.get_commit_parent(commit_hash)
        sed_command = f's/^pick {commit_hash[:7]}/edit {commit_hash[:7]}/'
        with self.interactive_rebase(parent_hash, sed_command, auto_continue=False):
            pass

    def start_interactive_rebase_at_commit(self, commit_hash: str):
        sed_command = f's/^pick {commit_hash[:7]}/edit {commit_hash[:7]}/'
        with self.interactive_rebase(f'{commit_hash}~1', sed_command, auto_continue=False):
            pass

    def amend_commit(self, message: str):
        with self.stage_and_commit(message, amend=True):
            pass

    def apply_patch_and_continue_rebase(self, patch_content: str, message: str):
        import tempfile
        patch_file = tempfile.NamedTemporaryFile(mode='w', suffix='.patch', delete=False)
        patch_path = patch_file.name

        try:
            patch_file.write(patch_content)
            patch_file.close()

            self.run(['apply', patch_path])
            with self.stage_and_commit(message, amend=True):
                pass

            if self.is_rebase_in_progress():
                self.continue_rebase()
        except Exception:
            if self.is_rebase_in_progress():
                self.abort_rebase()
            raise
        finally:
            if os.path.exists(patch_path):
                os.unlink(patch_path)

    def _get_status_lines(self):
        status_result = self.run(['status', '--porcelain'])
        return status_result.stdout.strip().split('\n') if status_result.stdout.strip() else []

    @staticmethod
    def _parse_porcelain_status_line(line: str):
        if not line or len(line) < 3:
            return None
        status_code = line[:2]
        file_path = line[2:].lstrip()
        return status_code, file_path

    @staticmethod
    def _decode_file_status(status_code: str):
        code = status_code[0] if status_code else 'M'
        if code == 'A':
            return 'added'
        if code == 'D':
            return 'deleted'
        if code == 'R':
            return 'renamed'
        return 'modified'

    @staticmethod
    def _parse_numstat_output(stdout: str):
        text = stdout.strip()
        if not text:
            return 0, 0
        first_line = text.split('\n')[0]
        parts = first_line.split('\t')
        if len(parts) >= 2:
            additions_text, deletions_text = parts[0], parts[1]
            additions = int(additions_text) if additions_text != '-' else 0
            deletions = int(deletions_text) if deletions_text != '-' else 0
            return additions, deletions
        return 0, 0

    def _get_file_diff_stats(self, file_path: str):
        diff_result = self.run(['diff', '--numstat', file_path])
        additions, deletions = self._parse_numstat_output(diff_result.stdout)
        if additions or deletions:
            return additions, deletions

        staged_diff_result = self.run(['diff', '--cached', '--numstat', file_path])
        return self._parse_numstat_output(staged_diff_result.stdout)


def init_five_git_repo(five_path: str):
    git_dir = os.path.join(five_path, '.git')
    subprocess.run(['git', 'init', five_path], check=True)
    return git_dir


def setup_five_gitignore(five_path: str, project_path: str, dont_track: bool):
    project_gitignore = os.path.join(project_path, '.gitignore')
    five_gitignore = os.path.join(five_path, '.fivegitignore')

    if os.path.exists(project_gitignore):
        with open(project_gitignore, 'r', encoding='utf-8') as f:
            original_content = f.read().strip()
            if original_content:
                original_content = f'# Original project .gitignore\n{original_content}'
    else:
        original_content = '# Original project .gitignore'

    if dont_track:
        relative_five_location = os.path.relpath(five_path, start=project_path)
        if not relative_five_location.endswith('/'):
            relative_five_location = relative_five_location + '/'
        new_content = f'# Do not track Five directory\n{relative_five_location}'
    else:
        new_content = ''

    gitignore_content = f"""
{original_content}
{FIVE_GITIGNORE_SEPARATOR}
{new_content}
""".strip() + '\n'

    with open(five_gitignore, 'w', encoding='utf-8') as f:
        f.write(gitignore_content)

    return five_gitignore


def configure_git_excludes_file(git_dir: str, work_tree: str, five_gitignore_path: str):
    repo = GitRepo(git_dir, work_tree)
    repo.run(['config', 'core.excludesFile', five_gitignore_path])


def create_initial_commit(git_dir: str, project_path: str, initial_message: str):
    repo = GitRepo(git_dir, project_path)
    with repo.stage_and_commit(initial_message):
        pass
    commit_hash_result = repo.run(['rev-parse', 'HEAD'])
    return commit_hash_result.stdout.strip()


def is_rebase_in_progress(git_dir: str) -> bool:
    rebase_merge_dir = os.path.join(git_dir, 'rebase-merge')
    rebase_apply_dir = os.path.join(git_dir, 'rebase-apply')
    return os.path.exists(rebase_merge_dir) or os.path.exists(rebase_apply_dir)
