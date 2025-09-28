"""
State management for the LangGraph orchestrator
"""
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum


class AgentEventType(Enum):
    """Types of agent events"""
    RUN_STARTED = "run_started"
    LLM_MESSAGE = "llm_message"
    ACTION_CALL = "action_call"
    ACTION_RESULT = "action_result"
    FINAL_MESSAGE = "final_message"
    RUN_COMPLETED = "run_completed"


@dataclass
class AgentEvent:
    """Base agent event"""
    type: AgentEventType
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for JSON serialization"""
        result = {"type": self.type.value}
        for key, value in self.__dict__.items():
            if key != "type":
                result[key] = value
        return result


@dataclass
class RunStartedEvent(AgentEvent):
    """Event emitted when a run starts"""
    run_id: str
    input_text: str
    
    def __post_init__(self):
        self.type = AgentEventType.RUN_STARTED


@dataclass
class LLMMessageEvent(AgentEvent):
    """Event emitted when LLM generates a message"""
    node: str  # "planner" or "synthesizer"
    content: str
    
    def __post_init__(self):
        self.type = AgentEventType.LLM_MESSAGE


@dataclass
class ActionCallEvent(AgentEvent):
    """Event emitted when an action is called"""
    name: str
    args: Dict[str, Any]
    
    def __post_init__(self):
        self.type = AgentEventType.ACTION_CALL


@dataclass
class ActionResultEvent(AgentEvent):
    """Event emitted when an action completes"""
    name: str
    ok: bool
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    
    def __post_init__(self):
        self.type = AgentEventType.ACTION_RESULT


@dataclass
class FinalMessageEvent(AgentEvent):
    """Event emitted with the final message"""
    content: str
    
    def __post_init__(self):
        self.type = AgentEventType.FINAL_MESSAGE


@dataclass
class RunCompletedEvent(AgentEvent):
    """Event emitted when a run completes"""
    status: str  # "ok" or "error"
    error: Optional[str] = None
    
    def __post_init__(self):
        self.type = AgentEventType.RUN_COMPLETED


@dataclass
class AgentState:
    """State object for the agent orchestrator"""
    # Input
    input_text: str
    session_id: Optional[str] = None
    domain: Optional[str] = None
    
    # Events
    events: List[AgentEvent] = field(default_factory=list)
    
    # Run metadata
    run_id: Optional[str] = None
    
    # LLM outputs
    planner_output: Optional[Dict[str, Any]] = None
    synthesizer_output: Optional[str] = None
    
    # Action execution
    actions_to_execute: List[Dict[str, Any]] = field(default_factory=list)
    action_results: List[Dict[str, Any]] = field(default_factory=list)
    
    # Final output
    final_message: Optional[str] = None
    
    def add_event(self, event: AgentEvent):
        """Add an event to the state"""
        self.events.append(event)
    
    def get_events_dict(self) -> List[Dict[str, Any]]:
        """Get events as list of dictionaries"""
        return [event.to_dict() for event in self.events]
    
    def to_response_dict(self) -> Dict[str, Any]:
        """Convert state to API response format"""
        return {
            "events": self.get_events_dict(),
            "final_message": self.final_message or "",
            "state_patch": {
                "run_id": self.run_id,
                "session_id": self.session_id,
                "domain": self.domain
            }
        }
