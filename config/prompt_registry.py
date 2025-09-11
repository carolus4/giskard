"""
Centralized prompt registry for tracking prompt performance over time
"""

from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import os


@dataclass
class PromptConfig:
    """Configuration for a specific prompt attempt"""
    name: str
    version: str
    goal: str
    model: str
    temperature: float
    token_limit: int
    top_k: Optional[int] = None
    top_p: Optional[float] = None
    prompt: str = ""
    output: Optional[str] = None
    created_at: Optional[datetime] = None
    performance_metrics: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        if self.created_at:
            data['created_at'] = self.created_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PromptConfig':
        """Create from dictionary"""
        if 'created_at' in data and data['created_at']:
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        return cls(**data)


class PromptRegistry:
    """Registry for managing and tracking prompt performance"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.prompts_file = os.path.join(data_dir, "prompt_registry.json")
        self.performance_file = os.path.join(data_dir, "prompt_performance.json")
        self._prompts: Dict[str, List[PromptConfig]] = {}
        self._performance_log: List[Dict[str, Any]] = []
        self._load_data()

    def _load_data(self):
        """Load existing prompts and performance data"""
        # Load prompts
        if os.path.exists(self.prompts_file):
            try:
                with open(self.prompts_file, 'r') as f:
                    data = json.load(f)
                    for name, prompt_list in data.items():
                        self._prompts[name] = [PromptConfig.from_dict(p) for p in prompt_list]
            except Exception as e:
                print(f"Error loading prompts: {e}")
                self._prompts = {}

        # Load performance data
        if os.path.exists(self.performance_file):
            try:
                with open(self.performance_file, 'r') as f:
                    self._performance_log = json.load(f)
            except Exception as e:
                print(f"Error loading performance data: {e}")
                self._performance_log = []

    def _save_data(self):
        """Save prompts and performance data to files"""
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Save prompts
        prompts_data = {}
        for name, prompt_list in self._prompts.items():
            prompts_data[name] = [p.to_dict() for p in prompt_list]
        
        with open(self.prompts_file, 'w') as f:
            json.dump(prompts_data, f, indent=2)

        # Save performance data
        with open(self.performance_file, 'w') as f:
            json.dump(self._performance_log, f, indent=2)

    def register_prompt(self, prompt_config: PromptConfig) -> str:
        """Register a new prompt configuration"""
        if prompt_config.name not in self._prompts:
            self._prompts[prompt_config.name] = []
        
        self._prompts[prompt_config.name].append(prompt_config)
        self._save_data()
        
        return f"{prompt_config.name}_v{prompt_config.version}"

    def get_prompt(self, name: str, version: Optional[str] = None) -> Optional[PromptConfig]:
        """Get a specific prompt by name and optionally version"""
        if name not in self._prompts:
            return None
        
        if version is None:
            # Return the latest version
            return self._prompts[name][-1] if self._prompts[name] else None
        
        # Return specific version
        for prompt in self._prompts[name]:
            if prompt.version == version:
                return prompt
        return None

    def get_latest_prompt(self, name: str) -> Optional[PromptConfig]:
        """Get the latest version of a prompt"""
        if name not in self._prompts or not self._prompts[name]:
            return None
        return self._prompts[name][-1]

    def list_prompts(self) -> List[str]:
        """List all available prompt names"""
        return list(self._prompts.keys())

    def get_prompt_versions(self, name: str) -> List[PromptConfig]:
        """Get all versions of a specific prompt"""
        return self._prompts.get(name, [])

    def log_performance(self, prompt_name: str, prompt_version: str, 
                       output: str, metrics: Optional[Dict[str, Any]] = None):
        """Log performance data for a prompt execution"""
        performance_entry = {
            "timestamp": datetime.now().isoformat(),
            "prompt_name": prompt_name,
            "prompt_version": prompt_version,
            "output": output,
            "metrics": metrics or {}
        }
        
        self._performance_log.append(performance_entry)
        self._save_data()

    def get_performance_history(self, prompt_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get performance history, optionally filtered by prompt name"""
        if prompt_name is None:
            return self._performance_log
        
        return [entry for entry in self._performance_log 
                if entry.get('prompt_name') == prompt_name]

    def get_performance_summary(self, prompt_name: str) -> Dict[str, Any]:
        """Get performance summary for a specific prompt"""
        history = self.get_performance_history(prompt_name)
        
        if not history:
            return {"total_executions": 0}
        
        return {
            "total_executions": len(history),
            "latest_execution": history[-1]["timestamp"] if history else None,
            "first_execution": history[0]["timestamp"] if history else None,
            "average_output_length": sum(len(entry.get("output", "")) for entry in history) / len(history)
        }


# Global registry instance
prompt_registry = PromptRegistry()


# Predefined prompt configurations
def create_coaching_prompt_v1() -> PromptConfig:
    """Create the coaching system prompt v1"""
    return PromptConfig(
        name="coaching_system",
        version="1.0",
        goal="Provide supportive productivity coaching and task management advice",
        model="llama3.1:8b",
        temperature=0.7,
        token_limit=500,
        top_p=0.9,
        prompt="""You are Giscard, a productivity coach and personal assistant. You help users manage their tasks, stay motivated, and achieve their goals.

Your personality:
- Supportive and encouraging, but not overly cheerful
- Direct and practical in your advice
- Focused on productivity and getting things done
- Understanding of the challenges of task management

Current task context:
{task_context}

Guidelines:
- Keep responses concise and actionable
- Offer specific advice based on the user's tasks and their descriptions
- Use task descriptions to provide more targeted productivity advice
- Suggest prioritization, time management, and productivity techniques
- Be empathetic to productivity struggles
- Don't make assumptions about tasks you can't see
- If asked about tasks, refer to what you can see in the context above
- When multiple tasks have similar descriptions, suggest grouping or batching them

Remember: You now have access to both task titles AND descriptions, so you can provide much more personalized and specific advice based on the actual work content."""
    )


def create_classification_prompt_v1() -> PromptConfig:
    """Create the task classification prompt v1"""
    return PromptConfig(
        name="task_classification",
        version="1.0",
        goal="Classify tasks into health, career, and learning categories with high precision",
        model="llama3.1:8b",
        temperature=0.1,
        token_limit=100,
        top_p=0.9,
        prompt="""You are a task categorization assistant. Your job is to assign 0..n labels from {{health, career, learning}} to each task.

Guidelines:
- Be conservative: only assign categories if you're confident
- If unsure, assign no categories (empty list)
- High precision is more important than recall
- Consider the task content, not just keywords

Categories:
- health: Physical health, fitness, medical, wellness, self-care
- career: Work, networking, interviews, interview prep, applications, job-related, business
- learning: Education, skill development, studying, knowledge acquisition, personal projects including 'Giskard' (the AI assistant)

Task: "{task_text}"

Respond with ONLY a valid JSON array of category strings. Examples:
- ["health"] for "Go to the gym"
- ["career", "learning"] for "Complete Python certification course"
- [] for "Buy groceries"

JSON:"""
    )


def initialize_default_prompts():
    """Initialize the registry with default prompts"""
    # Register coaching prompt
    coaching_prompt = create_coaching_prompt_v1()
    prompt_registry.register_prompt(coaching_prompt)
    
    # Register classification prompt
    classification_prompt = create_classification_prompt_v1()
    prompt_registry.register_prompt(classification_prompt)
    
    print("Default prompts initialized in registry")


# Initialize default prompts when module is imported (only if registry is empty)
if __name__ != "__main__":
    if not prompt_registry.list_prompts():
        initialize_default_prompts()
