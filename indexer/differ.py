import sys
import os
import re


class DiffOperation:
    def __init__(
        self, filepath: str, start_line: int, end_line: int, content: list[str]
    ):
        self.filepath = filepath
        self.start_line = start_line
        self.end_line = end_line
        self.content = content

    def __repr__(self):
        return f"DiffOperation({self.filepath}, {self.start_line}+{self.end_line})"


class DiffParser:
    HEADER_PATTERN = re.compile(
        r"^======(?P<filepath>.+):(?P<start_line>\d+)\+(?P<end_line>\d+)$"
    )
    END_MARKER = "======end"

    def __init__(self, project_path: str = None):
        self.project_path = project_path

    def parse_stdin(self) -> list[DiffOperation]:
        operations = []
        lines = [line.rstrip("\n") for line in sys.stdin.readlines()]
        i = 0

        while i < len(lines):
            if lines[i].startswith("======") and not lines[i] == self.END_MARKER:
                operation, next_i = self._parse_operation(lines, i)
                operations.append(operation)
                i = next_i
            else:
                i += 1

        return operations

    def _parse_operation(
        self, lines: list[str], start_idx: int
    ) -> tuple[DiffOperation, int]:
        header_line = lines[start_idx]
        match = self.HEADER_PATTERN.match(header_line)

        if not match:
            raise ValueError(f"Invalid diff header format: {header_line}")

        filepath = match.group("filepath")
        start_line = int(match.group("start_line"))
        end_line = int(match.group("end_line"))

        if start_line > end_line:
            raise ValueError(
                f"Start line cannot be greater than end line: {start_line}+{end_line}"
            )

        if self.project_path:
            filepath = os.path.join(self.project_path, filepath)

        content = []
        i = start_idx + 1

        while i < len(lines):
            if lines[i] == self.END_MARKER:
                break
            content.append(lines[i])
            i += 1
        else:
            raise ValueError(f"Missing end marker for operation on {filepath}")

        return DiffOperation(filepath, start_line, end_line, content), i + 1


class FileEditor:
    def __init__(self):
        self.file_operations: dict[str, list[DiffOperation]] = {}

    def add_operations(self, operations: list[DiffOperation]):
        for op in operations:
            if op.filepath not in self.file_operations:
                self.file_operations[op.filepath] = []
            self.file_operations[op.filepath].append(op)

    def validate_operations(self):
        for filepath, ops in self.file_operations.items():
            self._validate_file_operations(filepath, ops)

    def _validate_file_operations(self, filepath: str, operations: list[DiffOperation]):
        if not os.path.exists(filepath):
            raise ValueError(f"File does not exist: {filepath}")

        if not os.path.isfile(filepath):
            raise ValueError(f"Path is not a file: {filepath}")

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except (IOError, UnicodeDecodeError) as e:
            raise ValueError(f"Cannot read file {filepath}: {e}")

        if not lines:
            raise ValueError(f"File is empty: {filepath}")

        line_count = len(lines)

        for op in operations:
            if op.start_line > line_count:
                raise ValueError(
                    f"Start line {op.start_line} exceeds file length {line_count} in {filepath}"
                )
            if op.end_line > line_count:
                raise ValueError(
                    f"End line {op.end_line} exceeds file length {line_count} in {filepath}"
                )

        ranges = [(op.start_line, op.end_line) for op in operations]
        ranges.sort()

        for i in range(1, len(ranges)):
            if ranges[i][0] <= ranges[i - 1][1]:
                raise ValueError(f"Overlapping line ranges in {filepath}")

    def apply_operations(self) -> list[str]:
        modified_files = []

        for filepath, operations in self.file_operations.items():
            self._apply_file_operations(filepath, operations)
            modified_files.append(filepath)

        return sorted(modified_files)

    def _apply_file_operations(self, filepath: str, operations: list[DiffOperation]):
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()

        operations.sort(key=lambda op: op.start_line, reverse=True)

        for op in operations:
            start_idx = op.start_line - 1
            end_idx = op.end_line

            replacement = [line + "\n" for line in op.content]
            lines[start_idx:end_idx] = replacement

        with open(filepath, "w", encoding="utf-8") as f:
            f.writelines(lines)


def main():
    try:
        parser = DiffParser()
        operations = parser.parse_stdin()

        if not operations:
            print("No diff operations found in input", file=sys.stderr)
            return 1

        seen_files = set()
        for op in operations:
            if op.filepath in seen_files:
                raise ValueError(f"Duplicate file entry: {op.filepath}")
            seen_files.add(op.filepath)

        editor = FileEditor()
        editor.add_operations(operations)
        editor.validate_operations()

        modified_files = editor.apply_operations()

        for filepath in modified_files:
            print(filepath)

        return 0

    except (ValueError, IOError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nOperation cancelled", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
