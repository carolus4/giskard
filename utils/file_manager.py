"""
File operations and persistence for todo.txt
"""
from pathlib import Path
from typing import List
from models.task import TaskCollection


class TodoFileManager:
    """Handles file operations for todo.txt"""
    
    def __init__(self, file_path: str = "todo.txt"):
        self.file_path = Path(file_path)
        self.ensure_file()

    def ensure_file(self) -> None:
        """Ensure todo.txt exists"""
        if not self.file_path.exists():
            self.file_path.write_text("", encoding="utf-8")

    def read_lines(self) -> List[str]:
        """Read all lines from todo.txt"""
        self.ensure_file()
        content = self.file_path.read_text(encoding="utf-8").strip()
        if not content:
            return []
        return content.splitlines()

    def write_lines(self, lines: List[str]) -> None:
        """Write lines to todo.txt"""
        if lines:
            # Filter out empty lines for cleaner file
            non_empty_lines = [line for line in lines if line.strip()]
            if non_empty_lines:
                self.file_path.write_text("\n".join(non_empty_lines) + "\n", encoding="utf-8")
            else:
                self.file_path.write_text("", encoding="utf-8")
        else:
            self.file_path.write_text("", encoding="utf-8")

    def load_tasks(self) -> TaskCollection:
        """Load tasks from file"""
        lines = self.read_lines()
        collection = TaskCollection.from_lines(lines)
        
        # Auto-assign missing orders
        collection.assign_missing_orders()
        
        return collection

    def save_tasks(self, collection: TaskCollection) -> None:
        """Save tasks to file"""
        lines = collection.to_lines()
        self.write_lines(lines)

    def backup_file(self, suffix: str = None) -> Path:
        """Create a backup of the current todo.txt file"""
        if suffix is None:
            from datetime import datetime
            suffix = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        backup_path = self.file_path.with_name(f"{self.file_path.stem}_backup_{suffix}{self.file_path.suffix}")
        if self.file_path.exists():
            backup_path.write_text(self.file_path.read_text(encoding="utf-8"), encoding="utf-8")
        
        return backup_path
