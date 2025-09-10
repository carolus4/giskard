"""
Task model and parsing logic
"""
from datetime import datetime
from typing import Optional, Tuple, List, Dict, Any


class Task:
    """Represents a todo task with parsing and formatting capabilities"""
    
    def __init__(self, title: str, description: str = "", order: Optional[int] = None, 
                 status: str = 'open', completion_date: Optional[str] = None, file_idx: Optional[int] = None,
                 categories: Optional[List[str]] = None):
        self.title = title
        self.description = description
        self.order = order
        self.status = status  # 'open', 'in_progress', 'done'
        self.completion_date = completion_date
        self.file_idx = file_idx
        self.categories = categories or []  # List of categories: health, career, learning

    @classmethod
    def from_line(cls, line: str, file_idx: int) -> 'Task':
        """Parse a single line from data/todo.txt into a Task object"""
        line = line.strip()
        if not line:
            raise ValueError("Empty line cannot be parsed as task")
        
        if line.startswith("x "):
            # Completed task
            return cls._parse_completed_task(line, file_idx)
        elif "status:in_progress" in line:
            # In progress task
            return cls._parse_in_progress_task(line, file_idx)
        else:
            # Open task
            title, description, order, categories = cls._parse_task_text(line)
            return cls(title, description, order, 'open', file_idx=file_idx, categories=categories)

    @classmethod
    def _parse_completed_task(cls, line: str, file_idx: int) -> 'Task':
        """Parse a completed task line"""
        parts = line[2:].strip().split(" ", 1)
        if len(parts) >= 2 and parts[0].count('-') == 2:
            # Has date format YYYY-MM-DD
            completion_date = parts[0]
            task_text = parts[1]
        else:
            # No date, everything after "x " is the task text
            completion_date = None
            task_text = line[2:].strip()
        
        title, description, order, categories = cls._parse_task_text(task_text)
        return cls(title, description, order, 'done', completion_date, file_idx, categories)

    @classmethod
    def _parse_in_progress_task(cls, line: str, file_idx: int) -> 'Task':
        """Parse an in-progress task line"""
        task_text = line.replace("status:in_progress", "").strip()
        title, description, order, categories = cls._parse_task_text(task_text)
        return cls(title, description, order, 'in_progress', file_idx=file_idx, categories=categories)

    @classmethod
    def _parse_task_text(cls, text: str) -> Tuple[str, str, Optional[int], List[str]]:
        """Parse task text to extract title, description, order, and categories from new canonical format"""
        import re
        
        # Check if this is the new canonical format (has project: tag)
        if "project:" in text:
            return cls._parse_canonical_format(text)
        
        # Fallback to old format for backward compatibility
        if " | " in text:
            parts = text.split(" | ")
            title = parts[0].strip()
            description = parts[1].replace("\\n", "\n").strip() if len(parts) > 1 else ""
            # Check if there's an order number (third part)
            order = None
            if len(parts) >= 3 and parts[2].strip().isdigit():
                order = int(parts[2].strip())
            return title, description, order, []
        return text.strip(), "", None, []
    
    @classmethod
    def _parse_canonical_format(cls, text: str) -> Tuple[str, str, Optional[int], List[str]]:
        """Parse the new canonical format: project:"name" title note:"description" categories:"health,career" status:in_progress"""
        import re
        
        # Extract project name
        project_match = re.search(r'project:"([^"]*)"|project:(\S+)', text)
        project = ""
        if project_match:
            project = project_match.group(1) or project_match.group(2)
            # Remove project tag from text
            text = re.sub(r'project:"[^"]*"|project:\S+', '', text).strip()
        
        # Extract note/description
        note_match = re.search(r'note:"([^"]*)"|note:(\S+)', text)
        description = ""
        if note_match:
            description = note_match.group(1) or note_match.group(2)
            # Remove note tag from text
            text = re.sub(r'note:"[^"]*"|note:\S+', '', text).strip()
        
        # Extract categories
        categories_match = re.search(r'categories:"([^"]*)"|categories:(\S+)', text)
        categories = []
        if categories_match:
            categories_str = categories_match.group(1) or categories_match.group(2)
            if categories_str and categories_str != '""':
                categories = [cat.strip() for cat in categories_str.split(',') if cat.strip()]
            # Remove categories tag from text
            text = re.sub(r'categories:"[^"]*"|categories:\S+', '', text).strip()
        
        # Extract other tags (status, time_minutes, etc.) and remove them
        text = re.sub(r'\s+(?:status|time_minutes|created):[^\s]+', '', text).strip()
        
        # What's left is the title
        title = text.strip()
        
        # Format title as [Project] Title if project exists
        if project and project != '""':
            title = f"[{project}] {title}"
        
        return title, description, None, categories

    def to_line(self) -> str:
        """Format task back to data/todo.txt line format"""
        task_text = self._format_task_text()
        
        if self.status == 'done':
            if self.completion_date:
                return f"x {self.completion_date} {task_text}"
            else:
                return f"x {task_text}"
        elif self.status == 'in_progress':
            return f"{task_text} status:in_progress"
        else:
            return task_text

    def _format_task_text(self) -> str:
        """Format task title, description, and order for storage in new canonical format"""
        import re
        
        # Extract project from title if it's in [Project] format
        project = ""
        title = self.title
        project_match = re.match(r'^\[([^\]]+)\]\s*(.+)$', self.title)
        if project_match:
            project = project_match.group(1)
            title = project_match.group(2)
        
        # Build canonical format
        parts = []
        
        # Add project tag
        if project:
            if ' ' in project:
                parts.append(f'project:"{project}"')
            else:
                parts.append(f'project:{project}')
        else:
            parts.append('project:""')
        
        # Add title
        parts.append(title)
        
        # Add note tag if description exists
        if self.description:
            escaped_description = self.description.replace("\n", "\\n")
            if ' ' in escaped_description:
                parts.append(f'note:"{escaped_description}"')
            else:
                parts.append(f'note:{escaped_description}')
        
        # Add categories tag if categories exist
        if self.categories:
            categories_str = ','.join(self.categories)
            if ' ' in categories_str:
                parts.append(f'categories:"{categories_str}"')
            else:
                parts.append(f'categories:{categories_str}')
        
        return ' '.join(parts)

    def mark_done(self, completion_date: Optional[str] = None) -> None:
        """Mark task as done with optional completion date"""
        self.status = 'done'
        self.completion_date = completion_date or datetime.now().strftime("%Y-%m-%d")

    def mark_in_progress(self) -> None:
        """Mark task as in progress"""
        self.status = 'in_progress'
        self.completion_date = None

    def mark_open(self) -> None:
        """Mark task as open"""
        self.status = 'open'
        self.completion_date = None

    def update_content(self, title: str, description: str = "") -> None:
        """Update task title and description"""
        self.title = title.strip()
        self.description = description.strip()

    def to_dict(self, ui_id: Optional[int] = None) -> Dict[str, Any]:
        """Convert task to dictionary for API responses"""
        result = {
            'file_idx': self.file_idx,
            'title': self.title,
            'description': self.description,
            'order': self.order,
            'status': self.status,
            'categories': self.categories
        }
        
        if ui_id is not None:
            result['id'] = ui_id
            
        if self.completion_date:
            result['completion_date'] = self.completion_date
            
        return result

    def __repr__(self) -> str:
        return f"Task(title='{self.title}', status='{self.status}', order={self.order})"


class TaskCollection:
    """Manages a collection of tasks with parsing and ordering capabilities"""
    
    def __init__(self, tasks: List[Task] = None):
        self.tasks = tasks or []

    @classmethod
    def from_lines(cls, lines: List[str]) -> 'TaskCollection':
        """Create TaskCollection from data/todo.txt lines"""
        tasks = []
        for idx, line in enumerate(lines):
            line = line.strip()
            if line:  # Skip empty lines
                try:
                    task = Task.from_line(line, idx)
                    tasks.append(task)
                except ValueError:
                    # Skip invalid lines
                    continue
        return cls(tasks)

    def to_lines(self) -> List[str]:
        """Convert tasks back to data/todo.txt format lines"""
        # Create a list with empty slots for all possible file indices
        max_idx = max((t.file_idx for t in self.tasks), default=-1)
        lines = [''] * (max_idx + 1)
        
        # Fill in the tasks at their file indices
        for task in self.tasks:
            if task.file_idx is not None:
                lines[task.file_idx] = task.to_line()
        
        return lines

    def get_by_status(self) -> Tuple[List[Task], List[Task], List[Task]]:
        """Get tasks grouped by status: (open, in_progress, done) - File-Order-First approach"""
        open_tasks = [t for t in self.tasks if t.status == 'open']
        in_progress_tasks = [t for t in self.tasks if t.status == 'in_progress']
        done_tasks = [t for t in self.tasks if t.status == 'done']
        
        # For File-Order-First, sort by file_idx (file position)
        def sort_by_file_position(tasks):
            return sorted(tasks, key=lambda x: x.file_idx if x.file_idx is not None else float('inf'))
        
        # Sort completed tasks by completion date descending, then by file position
        def sort_completed_tasks(tasks):
            return sorted(tasks, key=lambda x: (x.completion_date or '', x.file_idx if x.file_idx is not None else float('inf')), reverse=True)
        
        return (sort_by_file_position(open_tasks), 
                sort_by_file_position(in_progress_tasks), 
                sort_completed_tasks(done_tasks))

    def assign_missing_orders(self) -> int:
        """Auto-assign order numbers to tasks that don't have them"""
        next_order = 1
        modified = False
        
        for task in self.tasks:
            if task.order is None:
                task.order = next_order
                modified = True
            next_order = max(next_order, (task.order or 0) + 1)
        
        return next_order

    def get_task_by_file_idx(self, file_idx: int) -> Optional[Task]:
        """Get task by its file index"""
        for task in self.tasks:
            if task.file_idx == file_idx:
                return task
        return None

    def add_task(self, title: str, description: str = "") -> Task:
        """Add a new task to the collection"""
        # Find the next available file index
        used_indices = {t.file_idx for t in self.tasks if t.file_idx is not None}
        next_idx = 0
        while next_idx in used_indices:
            next_idx += 1
        
        task = Task(title, description, file_idx=next_idx)
        self.tasks.append(task)
        return task

    def remove_task_by_file_idx(self, file_idx: int) -> bool:
        """Remove a task by its file index"""
        for i, task in enumerate(self.tasks):
            if task.file_idx == file_idx:
                del self.tasks[i]
                return True
        return False

    def reorder_tasks(self, new_order_sequence: List[int]) -> None:
        """Reorder tasks using a complete new order sequence"""
        # Create a mapping of old_order -> new_order
        order_mapping = {}
        for new_position, old_order in enumerate(new_order_sequence):
            order_mapping[old_order] = new_position + 1
        
        # Update orders based on the mapping
        for task in self.tasks:
            if task.order in order_mapping:
                task.order = order_mapping[task.order]

    def reorder_by_file_indices(self, file_idx_sequence: List[int]) -> None:
        """Reorder tasks using file indices in desired order - File-Order-First approach"""
        # For File-Order-First, we need to reorder the tasks list itself
        # Create a mapping of file_idx -> new position
        file_idx_to_position = {}
        for new_position, file_idx in enumerate(file_idx_sequence):
            file_idx_to_position[file_idx] = new_position
        
        # Sort tasks by their new position in the file
        def get_sort_key(task):
            if task.file_idx in file_idx_to_position:
                return file_idx_to_position[task.file_idx]
            else:
                # Keep tasks not in the sequence at the end
                return float('inf')
        
        # Sort tasks by their new file position
        self.tasks.sort(key=get_sort_key)
        
        # Update file_idx to match new positions
        for new_position, task in enumerate(self.tasks):
            task.file_idx = new_position

    def __len__(self) -> int:
        return len(self.tasks)

    def __iter__(self):
        return iter(self.tasks)
