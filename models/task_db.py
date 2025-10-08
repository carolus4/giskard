"""
Database models for tasks and agent steps using SQLite
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
import sqlite3
import json
from database import get_connection, get_next_sort_key


class TaskDB:
    """Database model for tasks with clean API"""
    
    def __init__(self, id: Optional[int] = None, title: str = "", description: str = "", 
                 status: str = 'open', sort_key: Optional[int] = None, project: Optional[str] = None,
                 categories: Optional[List[str]] = None, created_at: Optional[str] = None, 
                 updated_at: Optional[str] = None, started_at: Optional[str] = None,
                 completed_at: Optional[str] = None):
        self.id = id
        self.title = title
        self.description = description
        self.status = status
        self.sort_key = sort_key
        self.project = project
        self.categories = categories or []
        self.created_at = created_at or datetime.now().isoformat()
        self.updated_at = updated_at or datetime.now().isoformat()
        self.started_at = started_at
        self.completed_at = completed_at
    
    def save(self) -> 'TaskDB':
        """Save task to database (create or update)"""
        with get_connection() as conn:
            cursor = conn.cursor()
            
            now = datetime.now().isoformat()
            self.updated_at = now
            
            if self.id is None:
                # Create new task
                if self.sort_key is None:
                    self.sort_key = get_next_sort_key()
                
                cursor.execute('''
                    INSERT INTO tasks (title, description, status, sort_key, project, categories, 
                                     created_at, updated_at, started_at, completed_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (self.title, self.description, self.status, self.sort_key, self.project,
                      json.dumps(self.categories), self.created_at, self.updated_at, self.started_at, self.completed_at))
                
                self.id = cursor.lastrowid
            else:
                # Update existing task
                cursor.execute('''
                    UPDATE tasks SET title=?, description=?, status=?, sort_key=?, project=?, 
                                   categories=?, updated_at=?, started_at=?, completed_at=?
                    WHERE id=?
                ''', (self.title, self.description, self.status, self.sort_key, self.project,
                      json.dumps(self.categories), self.updated_at, self.started_at, self.completed_at, self.id))
            
            conn.commit()
        return self
    
    def delete(self) -> bool:
        """Delete task from database"""
        if self.id is None:
            return False
        
        with get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM tasks WHERE id=?', (self.id,))
            deleted = cursor.rowcount > 0
            
            conn.commit()
        return deleted
    
    def mark_done(self) -> 'TaskDB':
        """Mark task as done"""
        self.status = 'done'
        self.completed_at = datetime.now().isoformat()
        self.started_at = None  # Clear started_at when completed
        return self.save()
    
    def mark_in_progress(self) -> 'TaskDB':
        """Mark task as in progress"""
        self.status = 'in_progress'
        self.started_at = datetime.now().isoformat()
        self.completed_at = None  # Clear completed_at when started
        return self.save()
    
    def mark_open(self) -> 'TaskDB':
        """Mark task as open"""
        self.status = 'open'
        self.started_at = None
        self.completed_at = None
        return self.save()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary for API responses"""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'sort_key': self.sort_key,
            'project': self.project,
            'categories': self.categories,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'started_at': self.started_at,
            'completed_at': self.completed_at
        }
    
    @classmethod
    def get_by_id(cls, task_id: int) -> Optional['TaskDB']:
        """Get task by ID"""
        with get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, title, description, status, sort_key, project, categories,
                       created_at, updated_at, started_at, completed_at
                FROM tasks WHERE id=?
            ''', (task_id,))
            
            row = cursor.fetchone()
            
            if row:
                # Parse categories JSON
                categories = json.loads(row[6]) if row[6] else []
                return cls(row[0], row[1], row[2], row[3], row[4], row[5], categories, row[7], row[8], row[9], row[10])
            return None
    
    @classmethod
    def get_all(cls, status: Optional[str] = None) -> List['TaskDB']:
        """Get all tasks, optionally filtered by status"""
        with get_connection() as conn:
            cursor = conn.cursor()
            
            if status:
                cursor.execute('''
                    SELECT id, title, description, status, sort_key, project, categories,
                           created_at, updated_at, started_at, completed_at
                    FROM tasks WHERE status=?
                    ORDER BY sort_key ASC
                ''', (status,))
            else:
                cursor.execute('''
                    SELECT id, title, description, status, sort_key, project, categories,
                           created_at, updated_at, started_at, completed_at
                    FROM tasks
                    ORDER BY sort_key ASC
                ''')
            
            rows = cursor.fetchall()
            
            # Parse categories JSON for each row
            tasks = []
            for row in rows:
                categories = json.loads(row[6]) if row[6] else []
                tasks.append(cls(row[0], row[1], row[2], row[3], row[4], row[5], categories, row[7], row[8], row[9], row[10]))
            return tasks
    
    @classmethod
    def get_by_status(cls) -> tuple[List['TaskDB'], List['TaskDB'], List['TaskDB']]:
        """Get tasks grouped by status: (open, in_progress, done)"""
        open_tasks = cls.get_all('open')
        in_progress_tasks = cls.get_all('in_progress')
        done_tasks = cls.get_all('done')
        
        return open_tasks, in_progress_tasks, done_tasks
    
    @classmethod
    def reorder_tasks(cls, task_ids: List[int]) -> bool:
        """Reorder tasks by updating their sort_key values with gaps for efficiency"""
        if not task_ids:
            return False
        
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                
                # Update sort_key for each task with gaps of 1000
                # This allows for efficient insertion between tasks without updating all tasks
                for i, task_id in enumerate(task_ids):
                    new_sort_key = (i + 1) * 1000
                    cursor.execute('''
                        UPDATE tasks SET sort_key=?, updated_at=?
                        WHERE id=?
                    ''', (new_sort_key, datetime.now().isoformat(), task_id))
                
                conn.commit()
                return True
        except Exception as e:
            print(f"Error reordering tasks: {e}")
            return False
    
    @classmethod
    def create(cls, title: str, description: str = "", project: Optional[str] = None,
               categories: Optional[List[str]] = None) -> 'TaskDB':
        """Create a new task"""
        task = cls(
            title=title,
            description=description,
            project=project,
            categories=categories or [],
            status='open'
        )
        return task.save()
    
    def __repr__(self) -> str:
        return f"TaskDB(id={self.id}, title='{self.title}', status='{self.status}')"


class AgentStepDB:
    """Database model for agent workflow steps"""

    def __init__(self, id: Optional[int] = None, trace_id: str = "", step_number: int = 0,
                 step_type: str = "", timestamp: Optional[str] = None,
                 input_data: Optional[Dict[str, Any]] = None, output_data: Optional[Dict[str, Any]] = None,
                 rendered_prompt: Optional[str] = None, llm_input: Optional[Dict[str, Any]] = None,
                 llm_output: Optional[str] = None, llm_model: Optional[str] = None, error: Optional[str] = None):
        self.id = id
        self.trace_id = trace_id
        self.step_number = step_number
        self.step_type = step_type
        self.timestamp = timestamp or datetime.now().isoformat()
        self.input_data = input_data or {}
        self.output_data = output_data or {}
        self.rendered_prompt = rendered_prompt
        self.llm_input = llm_input or {}
        self.llm_output = llm_output
        self.llm_model = llm_model
        self.error = error

    def save(self) -> 'AgentStepDB':
        """Save agent step to database (create or update)"""
        with get_connection() as conn:
            cursor = conn.cursor()

            if self.id is None:
                # Create new step
                cursor.execute('''
                    INSERT INTO agent_steps (trace_id, step_number, step_type, timestamp,
                                           input_data, output_data, rendered_prompt, llm_input,
                                           llm_output, llm_model, error)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (self.trace_id, self.step_number, self.step_type, self.timestamp,
                      json.dumps(self.input_data), json.dumps(self.output_data),
                      self.rendered_prompt, json.dumps(self.llm_input),
                      self.llm_output, self.llm_model, self.error))

                self.id = cursor.lastrowid
            else:
                # Update existing step
                cursor.execute('''
                    UPDATE agent_steps SET trace_id=?, step_number=?, step_type=?,
                                          timestamp=?, input_data=?, output_data=?,
                                          rendered_prompt=?, llm_input=?, llm_output=?, llm_model=?, error=?
                    WHERE id=?
                ''', (self.trace_id, self.step_number, self.step_type, self.timestamp,
                      json.dumps(self.input_data), json.dumps(self.output_data),
                      self.rendered_prompt, json.dumps(self.llm_input),
                      self.llm_output, self.llm_model, self.error, self.id))

            conn.commit()
        return self

    def delete(self) -> bool:
        """Delete agent step from database"""
        if self.id is None:
            return False

        with get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute('DELETE FROM agent_steps WHERE id=?', (self.id,))
            deleted = cursor.rowcount > 0

            conn.commit()
        return deleted

    def to_dict(self) -> Dict[str, Any]:
        """Convert agent step to dictionary for API responses"""
        return {
            'id': self.id,
            'trace_id': self.trace_id,
            'step_number': self.step_number,
            'step_type': self.step_type,
            'timestamp': self.timestamp,
            'input_data': self.input_data,
            'output_data': self.output_data,
            'rendered_prompt': self.rendered_prompt,
            'llm_input': self.llm_input,
            'llm_output': self.llm_output,
            'llm_model': self.llm_model,
            'error': self.error
        }

    @classmethod
    def get_by_id(cls, step_id: int) -> Optional['AgentStepDB']:
        """Get agent step by ID"""
        with get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute('''
                SELECT id, trace_id, step_number, step_type, timestamp, input_data,
                       output_data, rendered_prompt, llm_input, llm_output, llm_model, error
                FROM agent_steps WHERE id=?
            ''', (step_id,))

            row = cursor.fetchone()

            if row:
                return cls(
                    id=row[0],
                    trace_id=row[1],
                    step_number=row[2],
                    step_type=row[3],
                    timestamp=row[4],
                    input_data=json.loads(row[5]) if row[5] else {},
                    output_data=json.loads(row[6]) if row[6] else {},
                    rendered_prompt=row[7],
                    llm_input=json.loads(row[8]) if row[8] else {},
                    llm_output=row[9],
                    llm_model=row[10],
                    error=row[11]
                )
            return None

    @classmethod
    def get_by_trace_id(cls, trace_id: str) -> List['AgentStepDB']:
        """Get all steps for a specific trace"""
        with get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute('''
                SELECT id, trace_id, step_number, step_type, timestamp, input_data,
                       output_data, rendered_prompt, llm_input, llm_output, llm_model, error
                FROM agent_steps WHERE trace_id=?
                ORDER BY step_number ASC
            ''', (trace_id,))

            rows = cursor.fetchall()
            steps = []
            for row in rows:
                steps.append(cls(
                    id=row[0],
                    trace_id=row[1],
                    step_number=row[2],
                    step_type=row[3],
                    timestamp=row[4],
                    input_data=json.loads(row[5]) if row[5] else {},
                    output_data=json.loads(row[6]) if row[6] else {},
                    rendered_prompt=row[7],
                    llm_input=json.loads(row[8]) if row[8] else {},
                    llm_output=row[9],
                    llm_model=row[10],
                    error=row[11]
                ))
            return steps

    @classmethod
    def get_next_step_number(cls, trace_id: str) -> int:
        """Get the next step number for a trace"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT MAX(step_number) FROM agent_steps WHERE trace_id=?', (trace_id,))
            result = cursor.fetchone()
            return (result[0] or 0) + 1

    @classmethod
    def create(cls, trace_id: str, step_number: int, step_type: str,
               input_data: Optional[Dict[str, Any]] = None, output_data: Optional[Dict[str, Any]] = None,
               rendered_prompt: Optional[str] = None, llm_input: Optional[Dict[str, Any]] = None,
               llm_output: Optional[str] = None, llm_model: Optional[str] = None, error: Optional[str] = None) -> 'AgentStepDB':
        """Create a new agent step"""
        step = cls(
            trace_id=trace_id,
            step_number=step_number,
            step_type=step_type,
            input_data=input_data or {},
            output_data=output_data or {},
            rendered_prompt=rendered_prompt,
            llm_input=llm_input or {},
            llm_output=llm_output,
            llm_model=llm_model,
            error=error
        )
        return step.save()

    def __repr__(self) -> str:
        return f"AgentStepDB(id={self.id}, trace_id='{self.trace_id}', step={self.step_number}, type='{self.step_type}')"
