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
        
    def is_ollama_available(self) -> bool:
        """Check if Ollama is running and accessible"""
        try:
            # Test with a simple request to check if Ollama is responding
            test_url = "http://localhost:11434/api/tags"
            response = requests.get(test_url, timeout=5)
            return response.status_code == 200
        except Exception:
            return False
    
    def warmup_model(self) -> bool:
        """Warm up the model by sending a simple request to keep it loaded"""
        try:
            warmup_prompt = "Classify this task: test"
            warmup_response = self._send_to_ollama(warmup_prompt)
            logger.info("Model warmup successful")
            return True
        except Exception as e:
            logger.warning(f"Model warmup failed: {str(e)}")
            return False
        
    def classify_task(self, title: str, description: str = "") -> List[str]:
        """
        Classify a task into categories: health, career, learning
        
        Returns:
            List of categories (0..n from {health, career, learning})
            Empty list if uncertain or no categories apply
        """
        try:
            # Skip very long tasks that are likely to timeout
            task_text = f"{title} - {description}" if description else title
            if len(task_text) > 1000:  # Skip tasks longer than 1000 characters
                logger.warning(f"Skipping very long task (>{len(task_text)} chars): {title[:50]}...")
                self._log_classification(title, description, [], "SKIPPED: Task too long")
                return []
            
            # Clean URLs from task text but don't skip the task
            import re
            # Remove URLs but keep the rest of the content
            cleaned_text = re.sub(r'https?://\S+|www\.\S+|\S+\.(com|org|net|edu|gov)\S*', '', task_text, flags=re.IGNORECASE)
            # Clean up extra spaces, newlines, and dashes
            cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
            # Remove trailing dashes, commas, and quotes
            cleaned_text = re.sub(r'[-\s,>]+$', '', cleaned_text)
            # Remove leading quotes and timestamps
            cleaned_text = re.sub(r'^[>\s]*\[\d+/\d+/\d+.*?\]\s*', '', cleaned_text)
            
            # If after cleaning we have very little content, skip
            if len(cleaned_text) < 10:
                logger.warning(f"Skipping task with insufficient content after URL removal: {title[:50]}...")
                self._log_classification(title, description, [], "SKIPPED: Insufficient content after URL removal")
                return []
            
            # Use cleaned text for classification
            task_text = cleaned_text
            
            # Build the prompt using cleaned text
            # Split cleaned text back into title and description if possible
            if ' - ' in cleaned_text:
                clean_title, clean_description = cleaned_text.split(' - ', 1)
            else:
                clean_title = cleaned_text
                clean_description = ""
            
            prompt = self._build_classification_prompt(clean_title, clean_description)
            
            # Send to Ollama
            response = self._send_to_ollama(prompt)
            
            # Parse response
            categories = self._parse_classification_response(response)
            
            # Log the classification
            self._log_classification(title, description, categories, response)
            
            return categories
            
        except Exception as e:
            logger.error(f"Classification failed for task '{title}': {str(e)}")
            # Try simple keyword-based classification as fallback
            fallback_categories = self._simple_keyword_classification(title, description)
            self._log_classification(title, description, fallback_categories, f"FALLBACK: {str(e)}")
            return fallback_categories
    
    def _simple_keyword_classification(self, title: str, description: str) -> List[str]:
        """Simple keyword-based classification as fallback"""
        text = f"{title} {description}".lower()
        
        categories = []
        
        # Health keywords
        health_keywords = ['gym', 'workout', 'exercise', 'run', 'swim', 'yoga', 'health', 'fitness', 'vitamin', 'doctor', 'therapy', 'mental health', 'wellness']
        if any(keyword in text for keyword in health_keywords):
            categories.append('health')
        
        # Career keywords
        career_keywords = ['job', 'interview', 'career', 'work', 'meeting', 'networking', 'application', 'resume', 'linkedin', 'professional', 'business', 'client', 'project']
        if any(keyword in text for keyword in career_keywords):
            categories.append('career')
        
        # Learning keywords
        learning_keywords = ['learn', 'study', 'course', 'book', 'read', 'tutorial', 'practice', 'skill', 'education', 'training', 'certification', 'research', 'blog', 'write']
        if any(keyword in text for keyword in learning_keywords):
            categories.append('learning')
        
        return categories
    
    def classify_tasks_batch(self, tasks: List[Dict[str, Any]]) -> Dict[int, List[str]]:
        """
        Classify multiple tasks in batch
        
        Args:
            tasks: List of task dictionaries with 'title', 'description', 'file_idx'
            
        Returns:
            Dictionary mapping file_idx to list of categories
        """
        results = {}
        
        # Process tasks one by one with small delays to prevent overwhelming the model
        for i, task in enumerate(tasks):
            file_idx = task.get('file_idx')
            title = task.get('title', '')
            description = task.get('description', '')
            
            if not title:
                continue
            
            try:
                categories = self.classify_task(title, description)
                results[file_idx] = categories
                
                # Add small delay between requests to prevent overwhelming the model
                if i < len(tasks) - 1:  # Don't delay after the last task
                    import time
                    time.sleep(0.5)  # 500ms delay between requests
                    
            except Exception as e:
                logger.error(f"Failed to classify task '{title}': {str(e)}")
                # Skip this task and continue with the next one
                results[file_idx] = []  # Default to empty categories on error
                continue
                
        return results
    
    def _build_classification_prompt(self, title: str, description: str) -> str:
        """Build the classification prompt for the LLM"""
        from config.prompts import get_classification_prompt
        
        task_text = title
        if description:
            task_text += f" - {description}"
        
        return get_classification_prompt(task_text)
    
    def _send_to_ollama(self, prompt: str, max_retries: int = 1) -> str:
        """Send request to Ollama API with retry logic"""
        from config.ollama_config import CLASSIFICATION_CONFIG, REQUEST_TIMEOUT
        import time
        
        payload = {
            **CLASSIFICATION_CONFIG,
            "prompt": prompt
        }
        
        for attempt in range(max_retries):
            try:
                # Use consistent timeout for all attempts
                timeout = REQUEST_TIMEOUT
                
                response = requests.post(self.ollama_url, json=payload, timeout=timeout)
                response.raise_for_status()
                
                result = response.json()
                return result.get('response', '').strip()
                
            except requests.exceptions.Timeout as e:
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) * 2  # Exponential backoff: 2, 4, 8 seconds
                    logger.warning(f"Timeout on attempt {attempt + 1}, retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    raise Exception(f"Failed to connect to Ollama after {max_retries} attempts: {str(e)}. Make sure Ollama is running with {self.model} model.")
                    
            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) * 2
                    logger.warning(f"Request failed on attempt {attempt + 1}, retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    raise Exception(f"Failed to connect to Ollama after {max_retries} attempts: {str(e)}. Make sure Ollama is running with {self.model} model.")
    
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
