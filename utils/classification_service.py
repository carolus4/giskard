"""
LLM-based task classification service using Ollama
"""
import json
import requests
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TaskClassificationService:
    """Service for automatically categorizing tasks using LLM"""
    
    def __init__(self, log_file: str = "data/classification_predictions_log.txt"):
        self.log_file = Path(log_file)
        from config.ollama_config import OLLAMA_BASE_URL, DEFAULT_MODEL
        self.ollama_url = OLLAMA_BASE_URL
        self.model = DEFAULT_MODEL
        
    def classify_task(self, title: str, description: str = "") -> List[str]:
        """
        Classify a task into categories: health, career, learning
        
        Returns:
            List of categories (0..n from {health, career, learning})
            Empty list if uncertain or no categories apply
        """
        try:
            # Build the prompt
            prompt = self._build_classification_prompt(title, description)
            
            # Send to Ollama
            response = self._send_to_ollama(prompt)
            
            # Parse response
            categories = self._parse_classification_response(response)
            
            # Log the classification
            self._log_classification(title, description, categories, response)
            
            return categories
            
        except Exception as e:
            logger.error(f"Classification failed for task '{title}': {str(e)}")
            self._log_classification(title, description, [], f"ERROR: {str(e)}")
            return []
    
    def classify_tasks_batch(self, tasks: List[Dict[str, Any]]) -> Dict[int, List[str]]:
        """
        Classify multiple tasks in batch
        
        Args:
            tasks: List of task dictionaries with 'title', 'description', 'file_idx'
            
        Returns:
            Dictionary mapping file_idx to list of categories
        """
        results = {}
        
        for task in tasks:
            file_idx = task.get('file_idx')
            title = task.get('title', '')
            description = task.get('description', '')
            
            if not title:
                continue
                
            categories = self.classify_task(title, description)
            results[file_idx] = categories
            
        return results
    
    def _build_classification_prompt(self, title: str, description: str) -> str:
        """Build the classification prompt for the LLM"""
        from config.prompts import CLASSIFICATION_PROMPT
        
        task_text = title
        if description:
            task_text += f" - {description}"
        
        return CLASSIFICATION_PROMPT.format(task_text=task_text)
    
    def _send_to_ollama(self, prompt: str) -> str:
        """Send request to Ollama API"""
        from config.ollama_config import CLASSIFICATION_CONFIG, REQUEST_TIMEOUT
        
        payload = {
            **CLASSIFICATION_CONFIG,
            "prompt": prompt
        }
        
        try:
            response = requests.post(self.ollama_url, json=payload, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            
            result = response.json()
            return result.get('response', '').strip()
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to connect to Ollama: {str(e)}. Make sure Ollama is running with {self.model} model.")
    
    def _parse_classification_response(self, response: str) -> List[str]:
        """Parse the LLM response and extract categories"""
        try:
            # Clean the response - remove any extra text before/after JSON
            response = response.strip()
            
            # Find JSON array in the response
            start_idx = response.find('[')
            end_idx = response.rfind(']') + 1
            
            if start_idx == -1 or end_idx == 0:
                logger.warning(f"No JSON array found in response: {response}")
                return []
            
            json_str = response[start_idx:end_idx]
            categories = json.loads(json_str)
            
            # Validate categories
            valid_categories = {'health', 'career', 'learning'}
            if isinstance(categories, list):
                valid_cats = [cat for cat in categories if cat in valid_categories]
                return valid_cats
            else:
                logger.warning(f"Invalid response format: {response}")
                return []
                
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON from response '{response}': {str(e)}")
            return []
        except Exception as e:
            logger.warning(f"Unexpected error parsing response '{response}': {str(e)}")
            return []
    
    def _log_classification(self, title: str, description: str, categories: List[str], raw_response: str):
        """Log the classification result to file"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        task_text = title
        if description:
            task_text += f" - {description}"
        
        log_entry = {
            "timestamp": timestamp,
            "task": task_text,
            "categories": categories,
            "raw_response": raw_response
        }
        
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry) + '\n')
        except Exception as e:
            logger.error(f"Failed to write to log file: {str(e)}")
    
    def is_ollama_available(self) -> bool:
        """Check if Ollama is available and running"""
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def get_available_models(self) -> List[str]:
        """Get list of available Ollama models"""
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            response.raise_for_status()
            data = response.json()
            return [model['name'] for model in data.get('models', [])]
        except:
            return []
