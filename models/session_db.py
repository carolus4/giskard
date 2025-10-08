"""
Database models for sessions and traces using SQLite
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
import sqlite3
import json
import uuid
from database import get_connection


class SessionDB:
    """Database model for user sessions"""
    
    def __init__(self, id: Optional[str] = None, user_id: Optional[str] = None,
                 created_at: Optional[str] = None, updated_at: Optional[str] = None,
                 metadata: Optional[Dict[str, Any]] = None):
        self.id = id or str(uuid.uuid4())
        self.user_id = user_id
        self.created_at = created_at or datetime.now().isoformat()
        self.updated_at = updated_at or datetime.now().isoformat()
        self.metadata = metadata or {}
    
    def save(self) -> 'SessionDB':
        """Save session to database (create or update)"""
        with get_connection() as conn:
            cursor = conn.cursor()
            
            now = datetime.now().isoformat()
            self.updated_at = now
            
            cursor.execute('''
                INSERT OR REPLACE INTO sessions (id, user_id, created_at, updated_at, metadata)
                VALUES (?, ?, ?, ?, ?)
            ''', (self.id, self.user_id, self.created_at, self.updated_at, json.dumps(self.metadata)))
            
            conn.commit()
        return self
    
    def delete(self) -> bool:
        """Delete session and all associated traces and steps"""
        with get_connection() as conn:
            cursor = conn.cursor()
            
            # Delete associated agent steps
            cursor.execute('DELETE FROM agent_steps WHERE session_id=?', (self.id,))
            
            # Delete associated traces
            cursor.execute('DELETE FROM traces WHERE session_id=?', (self.id,))
            
            # Delete session
            cursor.execute('DELETE FROM sessions WHERE id=?', (self.id,))
            deleted = cursor.rowcount > 0
            
            conn.commit()
        return deleted
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary for API responses"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'metadata': self.metadata
        }
    
    @classmethod
    def get_by_id(cls, session_id: str) -> Optional['SessionDB']:
        """Get session by ID"""
        with get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, user_id, created_at, updated_at, metadata
                FROM sessions WHERE id=?
            ''', (session_id,))
            
            row = cursor.fetchone()
            
            if row:
                return cls(
                    id=row[0],
                    user_id=row[1],
                    created_at=row[2],
                    updated_at=row[3],
                    metadata=json.loads(row[4]) if row[4] else {}
                )
            return None
    
    @classmethod
    def get_all(cls, user_id: Optional[str] = None) -> List['SessionDB']:
        """Get all sessions, optionally filtered by user_id"""
        with get_connection() as conn:
            cursor = conn.cursor()
            
            if user_id:
                cursor.execute('''
                    SELECT id, user_id, created_at, updated_at, metadata
                    FROM sessions WHERE user_id=?
                    ORDER BY updated_at DESC
                ''', (user_id,))
            else:
                cursor.execute('''
                    SELECT id, user_id, created_at, updated_at, metadata
                    FROM sessions
                    ORDER BY updated_at DESC
                ''')
            
            rows = cursor.fetchall()
            sessions = []
            for row in rows:
                sessions.append(cls(
                    id=row[0],
                    user_id=row[1],
                    created_at=row[2],
                    updated_at=row[3],
                    metadata=json.loads(row[4]) if row[4] else {}
                ))
            return sessions
    
    @classmethod
    def create(cls, user_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> 'SessionDB':
        """Create a new session"""
        session = cls(user_id=user_id, metadata=metadata)
        return session.save()
    
    def __repr__(self) -> str:
        return f"SessionDB(id='{self.id}', user_id='{self.user_id}')"


class TraceDB:
    """Database model for individual traces within a session"""
    
    def __init__(self, id: Optional[str] = None, session_id: str = "", user_message: str = "",
                 assistant_response: Optional[str] = None, created_at: Optional[str] = None,
                 completed_at: Optional[str] = None, status: str = "in_progress",
                 metadata: Optional[Dict[str, Any]] = None):
        self.id = id or str(uuid.uuid4())
        self.session_id = session_id
        self.user_message = user_message
        self.assistant_response = assistant_response
        self.created_at = created_at or datetime.now().isoformat()
        self.completed_at = completed_at
        self.status = status
        self.metadata = metadata or {}
    
    def save(self) -> 'TraceDB':
        """Save trace to database (create or update)"""
        with get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO traces (id, session_id, user_message, assistant_response,
                                             created_at, completed_at, status, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (self.id, self.session_id, self.user_message, self.assistant_response,
                  self.created_at, self.completed_at, self.status, json.dumps(self.metadata)))
            
            conn.commit()
        return self
    
    def mark_completed(self, assistant_response: str) -> 'TraceDB':
        """Mark trace as completed with assistant response"""
        self.assistant_response = assistant_response
        self.completed_at = datetime.now().isoformat()
        self.status = "completed"
        return self.save()
    
    def mark_failed(self, error: str) -> 'TraceDB':
        """Mark trace as failed with error message"""
        self.completed_at = datetime.now().isoformat()
        self.status = "failed"
        self.metadata["error"] = error
        return self.save()
    
    def delete(self) -> bool:
        """Delete trace and all associated agent steps"""
        with get_connection() as conn:
            cursor = conn.cursor()
            
            # Delete associated agent steps
            cursor.execute('DELETE FROM agent_steps WHERE trace_id=?', (self.id,))
            
            # Delete trace
            cursor.execute('DELETE FROM traces WHERE id=?', (self.id,))
            deleted = cursor.rowcount > 0
            
            conn.commit()
        return deleted
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert trace to dictionary for API responses"""
        return {
            'id': self.id,
            'session_id': self.session_id,
            'user_message': self.user_message,
            'assistant_response': self.assistant_response,
            'created_at': self.created_at,
            'completed_at': self.completed_at,
            'status': self.status,
            'metadata': self.metadata
        }
    
    @classmethod
    def get_by_id(cls, trace_id: str) -> Optional['TraceDB']:
        """Get trace by ID"""
        with get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, session_id, user_message, assistant_response, created_at,
                       completed_at, status, metadata
                FROM traces WHERE id=?
            ''', (trace_id,))
            
            row = cursor.fetchone()
            
            if row:
                return cls(
                    id=row[0],
                    session_id=row[1],
                    user_message=row[2],
                    assistant_response=row[3],
                    created_at=row[4],
                    completed_at=row[5],
                    status=row[6],
                    metadata=json.loads(row[7]) if row[7] else {}
                )
            return None
    
    @classmethod
    def get_by_session_id(cls, session_id: str) -> List['TraceDB']:
        """Get all traces for a session"""
        with get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, session_id, user_message, assistant_response, created_at,
                       completed_at, status, metadata
                FROM traces WHERE session_id=?
                ORDER BY created_at ASC
            ''', (session_id,))
            
            rows = cursor.fetchall()
            traces = []
            for row in rows:
                traces.append(cls(
                    id=row[0],
                    session_id=row[1],
                    user_message=row[2],
                    assistant_response=row[3],
                    created_at=row[4],
                    completed_at=row[5],
                    status=row[6],
                    metadata=json.loads(row[7]) if row[7] else {}
                ))
            return traces
    
    @classmethod
    def create(cls, session_id: str, user_message: str, metadata: Optional[Dict[str, Any]] = None) -> 'TraceDB':
        """Create a new trace"""
        trace = cls(session_id=session_id, user_message=user_message, metadata=metadata)
        return trace.save()
    
    def __repr__(self) -> str:
        return f"TraceDB(id='{self.id}', session_id='{self.session_id}', status='{self.status}')"


class AgentStepDB:
    """Updated database model for agent workflow steps with session support"""
    
    def __init__(self, id: Optional[int] = None, session_id: str = "", trace_id: str = "", 
                 step_number: int = 0, step_type: str = "", timestamp: Optional[str] = None,
                 input_data: Optional[Dict[str, Any]] = None, output_data: Optional[Dict[str, Any]] = None,
                 rendered_prompt: Optional[str] = None, llm_input: Optional[Dict[str, Any]] = None,
                 llm_output: Optional[str] = None, llm_model: Optional[str] = None, error: Optional[str] = None):
        self.id = id
        self.session_id = session_id
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
                    INSERT INTO agent_steps (session_id, trace_id, step_number, step_type, timestamp,
                                           input_data, output_data, rendered_prompt, llm_input,
                                           llm_output, llm_model, error)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (self.session_id, self.trace_id, self.step_number, self.step_type, self.timestamp,
                      json.dumps(self.input_data), json.dumps(self.output_data),
                      self.rendered_prompt, json.dumps(self.llm_input),
                      self.llm_output, self.llm_model, self.error))
                
                self.id = cursor.lastrowid
            else:
                # Update existing step
                cursor.execute('''
                    UPDATE agent_steps SET session_id=?, trace_id=?, step_number=?, step_type=?,
                                          timestamp=?, input_data=?, output_data=?,
                                          rendered_prompt=?, llm_input=?, llm_output=?, llm_model=?, error=?
                    WHERE id=?
                ''', (self.session_id, self.trace_id, self.step_number, self.step_type, self.timestamp,
                      json.dumps(self.input_data), json.dumps(self.output_data),
                      self.rendered_prompt, json.dumps(self.llm_input),
                      self.llm_output, self.llm_model, self.error, self.id))
            
            conn.commit()
        return self
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert agent step to dictionary for API responses"""
        return {
            'id': self.id,
            'session_id': self.session_id,
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
    def get_by_trace_id(cls, trace_id: str) -> List['AgentStepDB']:
        """Get all steps for a specific trace"""
        with get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, session_id, trace_id, step_number, step_type, timestamp, input_data,
                       output_data, rendered_prompt, llm_input, llm_output, llm_model, error
                FROM agent_steps WHERE trace_id=?
                ORDER BY step_number ASC
            ''', (trace_id,))
            
            rows = cursor.fetchall()
            steps = []
            for row in rows:
                steps.append(cls(
                    id=row[0],
                    session_id=row[1],
                    trace_id=row[2],
                    step_number=row[3],
                    step_type=row[4],
                    timestamp=row[5],
                    input_data=json.loads(row[6]) if row[6] else {},
                    output_data=json.loads(row[7]) if row[7] else {},
                    rendered_prompt=row[8],
                    llm_input=json.loads(row[9]) if row[9] else {},
                    llm_output=row[10],
                    llm_model=row[11],
                    error=row[12]
                ))
            return steps
    
    @classmethod
    def get_by_session_id(cls, session_id: str) -> List['AgentStepDB']:
        """Get all steps for a session"""
        with get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, session_id, trace_id, step_number, step_type, timestamp, input_data,
                       output_data, rendered_prompt, llm_input, llm_output, llm_model, error
                FROM agent_steps WHERE session_id=?
                ORDER BY timestamp ASC
            ''', (session_id,))
            
            rows = cursor.fetchall()
            steps = []
            for row in rows:
                steps.append(cls(
                    id=row[0],
                    session_id=row[1],
                    trace_id=row[2],
                    step_number=row[3],
                    step_type=row[4],
                    timestamp=row[5],
                    input_data=json.loads(row[6]) if row[6] else {},
                    output_data=json.loads(row[7]) if row[7] else {},
                    rendered_prompt=row[8],
                    llm_input=json.loads(row[9]) if row[9] else {},
                    llm_output=row[10],
                    llm_model=row[11],
                    error=row[12]
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
    def create(cls, session_id: str, trace_id: str, step_number: int, step_type: str,
               input_data: Optional[Dict[str, Any]] = None, output_data: Optional[Dict[str, Any]] = None,
               rendered_prompt: Optional[str] = None, llm_input: Optional[Dict[str, Any]] = None,
               llm_output: Optional[str] = None, llm_model: Optional[str] = None, error: Optional[str] = None) -> 'AgentStepDB':
        """Create a new agent step"""
        step = cls(
            session_id=session_id,
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
        return f"AgentStepDB(id={self.id}, session_id='{self.session_id}', trace_id='{self.trace_id}', step={self.step_number}, type='{self.step_type}')"
