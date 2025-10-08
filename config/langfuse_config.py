"""
Langfuse configuration and initialization for Giskard agent observability
"""
import os
import logging
from typing import Optional
from langfuse import Langfuse, get_client
from langfuse.langchain import CallbackHandler
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)


class LangfuseConfig:
    """Langfuse configuration manager"""
    
    def __init__(self):
        self.public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
        self.secret_key = os.getenv("LANGFUSE_SECRET_KEY")
        self.host = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
        self.enabled = bool(self.public_key and self.secret_key)
        
        if self.enabled:
            self._initialize_client()
        else:
            logger.warning("Langfuse not configured - set LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY environment variables")
    
    def _initialize_client(self):
        """Initialize the Langfuse client"""
        try:
            self.client = Langfuse(
                public_key=self.public_key,
                secret_key=self.secret_key,
                host=self.host
            )
            logger.info("✅ Langfuse client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Langfuse client: {e}")
            self.enabled = False
    
    def get_callback_handler(self, trace_id: Optional[str] = None, user_id: Optional[str] = None) -> Optional[CallbackHandler]:
        """
        Get a Langfuse callback handler for LangChain integration
        
        Args:
            trace_id: Optional trace ID to group related operations
            user_id: Optional user ID for user tracking
            
        Returns:
            CallbackHandler instance or None if Langfuse is disabled
        """
        if not self.enabled:
            return None
        
        try:
            handler = CallbackHandler()
            
            # Set trace and user context if provided
            if trace_id or user_id:
                # Use metadata to pass context to the handler
                handler.metadata = {}
                if trace_id:
                    handler.metadata["langfuse_trace_id"] = trace_id
                if user_id:
                    handler.metadata["langfuse_user_id"] = user_id
            
            return handler
        except Exception as e:
            logger.error(f"Failed to create Langfuse callback handler: {e}")
            return None
    
    def create_trace_context(self, name: str, trace_id: Optional[str] = None, user_id: Optional[str] = None, input_data: Optional[dict] = None):
        """
        Create a Langfuse trace context for the conversation
        
        Args:
            name: Name of the trace (e.g., "giskard-message")
            trace_id: Optional trace ID
            user_id: Optional user ID
            input_data: Optional input data for the trace
            
        Returns:
            Langfuse trace context or None if disabled
        """
        if not self.enabled:
            return None
        
        try:
            from langfuse.types import TraceContext
            return TraceContext(
                trace_id=trace_id,
                user_id=user_id,
                input=input_data
            )
        except Exception as e:
            logger.error(f"Failed to create Langfuse trace context: {e}")
            return None
    
    def flush(self):
        """Flush pending events to Langfuse"""
        if self.enabled:
            try:
                client = get_client()
                client.flush()
            except Exception as e:
                logger.error(f"Failed to flush Langfuse events: {e}")
    
    def shutdown(self):
        """Shutdown the Langfuse client"""
        if self.enabled:
            try:
                client = get_client()
                client.shutdown()
            except Exception as e:
                logger.error(f"Failed to shutdown Langfuse client: {e}")


# Global Langfuse configuration instance
langfuse_config = LangfuseConfig()
