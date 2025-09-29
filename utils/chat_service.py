"""
Chat service for handling conversations with Ollama
"""
import requests
import logging
from typing import List, Dict, Any
from config.ollama_config import get_chat_config, REQUEST_TIMEOUT

logger = logging.getLogger(__name__)

class ChatService:
    """Service for handling chat conversations with Ollama"""
    
    def __init__(self):
        self.config = get_chat_config()
        self.ollama_url = "http://localhost:11434/api/generate"
        
    def send_message(self, message: str, conversation_history: List[Dict[str, Any]] = None) -> str:
        """
        Send a message to Ollama and get a response
        
        Args:
            message: The user's message
            conversation_history: Previous conversation messages
            
        Returns:
            The AI's response
        """
        try:
            # Build the conversation context
            prompt = self._build_prompt(message, conversation_history or [])
            
            # Prepare the request payload
            payload = {
                "model": self.config["model"],
                "prompt": prompt,
                "stream": self.config["stream"],
                "options": self.config["options"]
            }
            
            logger.info(f"🤖 Sending chat request to Ollama with model: {self.config['model']}")
            
            # Send request to Ollama
            response = requests.post(
                self.ollama_url, 
                json=payload, 
                timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status()
            
            result = response.json()
            ai_response = result.get('response', '').strip()
            
            if not ai_response:
                return "I'm sorry, I didn't get a response. Please try again."
            
            logger.info("✅ Chat response received successfully")
            return ai_response
            
        except requests.exceptions.Timeout:
            logger.error("⏰ Chat request timed out")
            return "I'm having trouble connecting right now. Please check if Ollama is running and try again."
            
        except requests.exceptions.ConnectionError:
            logger.error("🔌 Failed to connect to Ollama")
            return "I'm having trouble connecting right now. Please check if Ollama is running with gemma3:4b and try again."
            
        except Exception as e:
            logger.error(f"❌ Chat request failed: {str(e)}")
            return f"I'm having trouble connecting right now. Please check if Ollama is running with {self.config['model']} and try again."
    
    def _build_prompt(self, message: str, conversation_history: List[Dict[str, Any]]) -> str:
        """
        Build the prompt for Ollama including conversation history
        
        Args:
            message: Current user message
            conversation_history: Previous conversation messages
            
        Returns:
            Formatted prompt string
        """
        # Get the coaching system prompt
        from config.prompts import get_coaching_prompt
        system_prompt = get_coaching_prompt(task_context)
        
        # Build conversation context
        conversation_context = ""
        if conversation_history:
            for msg in conversation_history[-6:]:  # Keep last 6 messages for context
                role = "User" if msg.get('type') == 'user' else "Assistant"
                content = msg.get('content', '')
                conversation_context += f"{role}: {content}\n"
        
        # Combine everything into the final prompt
        full_prompt = f"{system_prompt}\n\n"
        
        if conversation_context:
            full_prompt += f"Previous conversation:\n{conversation_context}\n"
        
        full_prompt += f"User: {message}\nAssistant:"
        
        return full_prompt
    
    def is_ollama_available(self) -> bool:
        """Check if Ollama is running and accessible"""
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            return response.status_code == 200
        except Exception:
            return False

