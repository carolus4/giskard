"""
Classification manager for handling task categorization queue and startup classification
"""
import asyncio
import threading
import time
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from models.task_db import TaskDB
from utils.classification_service import TaskClassificationService

logger = logging.getLogger(__name__)

class ClassificationManager:
    """Manages task classification queue and background processing"""

    def __init__(self):
        self.classification_service = TaskClassificationService()
        self.classification_queue = []
        self.deferred_tasks = {}  # task_id -> task_data for deferred processing
        self.is_processing = False
        self.processing_thread = None
        self.stop_event = threading.Event()
        self.deferred_timeout = 5  # seconds to wait before processing deferred tasks
        
    def start_background_processing(self):
        """Start background thread for processing classification queue"""
        if self.processing_thread and self.processing_thread.is_alive():
            return
            
        self.processing_thread = threading.Thread(target=self._process_queue_loop, daemon=True)
        self.processing_thread.start()
        logger.info("Classification background processing started")
    
    def stop_background_processing(self):
        """Stop background processing"""
        self.stop_event.set()
        if self.processing_thread and self.processing_thread.is_alive():
            self.processing_thread.join(timeout=5)
        logger.info("Classification background processing stopped")
    
    def classify_on_startup(self) -> int:
        """
        Classify all uncategorized tasks on startup
        
        Returns:
            Number of tasks classified
        """
        try:
            if not self.classification_service.is_ollama_available():
                logger.warning("Ollama not available, skipping startup classification")
                return 0
            
            # Get all tasks from database
            all_tasks = TaskDB.get_all()
            uncategorized_tasks = [task for task in all_tasks if not task.categories or len(task.categories) == 0]
            
            if not uncategorized_tasks:
                logger.info("No uncategorized tasks found")
                return 0
            
            logger.info(f"Found {len(uncategorized_tasks)} uncategorized tasks, starting classification...")
            
            # Prepare tasks for batch classification
            task_data = []
            for task in uncategorized_tasks:
                task_data.append({
                    'id': task.id,
                    'title': task.title,
                    'description': task.description
                })
            
            # Classify in batch
            results = self.classification_service.classify_tasks_batch(task_data)
            
            # Update tasks with categories
            updated_count = 0
            for task in uncategorized_tasks:
                if task.id in results:
                    task.categories = results[task.id]
                    if task.categories:  # Only count if categories were assigned
                        task.save()  # Save to database
                        updated_count += 1
            
            if updated_count > 0:
                logger.info(f"Classified {updated_count} tasks on startup")
            
            return updated_count
            
        except Exception as e:
            logger.error(f"Startup classification failed: {str(e)}")
            return 0
    
    def enqueue_classification(self, task: TaskDB, deferred: bool = False):
        """
        Add a task to the classification queue

        Args:
            task: TaskDB object to classify
            deferred: Whether to defer classification (for debounced updates)
        """
        task_data = {
            'id': task.id,
            'title': task.title,
            'description': task.description,
            'project': task.project,
            'timestamp': datetime.now(),
            'deferred': deferred
        }

        if deferred:
            # For deferred tasks, store in deferred_tasks dict and set a timeout
            self.deferred_tasks[task.id] = task_data
            # Set a timer to process this task after the deferred timeout
            threading.Timer(self.deferred_timeout, self._process_deferred_task, args=[task.id]).start()
            logger.debug(f"Deferred classification for task: {task.title} (will process in {self.deferred_timeout}s)")
        else:
            # Always enqueue for immediate classification - even if task already has categories
            # This allows re-classification when task content is updated
            self.classification_queue.append(task_data)
            logger.debug(f"Enqueued task for immediate classification: {task.title}")
    
    def enqueue_tasks_batch(self, tasks: List[TaskDB]):
        """
        Add multiple tasks to the classification queue
        
        Args:
            tasks: List of TaskDB objects to classify
        """
        for task in tasks:
            self.enqueue_classification(task)
    
    def _process_deferred_task(self, task_id: int):
        """Process a deferred task after timeout"""
        if task_id in self.deferred_tasks:
            task_data = self.deferred_tasks.pop(task_id)
            # Move from deferred to regular queue for processing
            self.classification_queue.append(task_data)
            logger.debug(f"Processing deferred task: {task_data.get('title', 'Unknown')}")

    def _process_queue_loop(self):
        """Background loop for processing classification queue"""
        while not self.stop_event.is_set():
            try:
                if self.classification_queue and not self.is_processing:
                    self._process_queue_batch()
                else:
                    time.sleep(1)  # Wait 1 second before checking again
            except Exception as e:
                logger.error(f"Error in classification queue processing: {str(e)}")
                time.sleep(5)  # Wait longer on error
    
    def _process_queue_batch(self):
        """Process a batch of tasks from the queue"""
        if not self.classification_queue:
            return
            
        if not self.classification_service.is_ollama_available():
            logger.warning("Ollama not available, skipping classification")
            self.classification_queue.clear()
            return
        
        # Warm up the model to ensure it's loaded and ready
        self.classification_service.warmup_model()
        
        self.is_processing = True
        
        try:
            # Take up to 5 tasks from the queue (reduced from 10 to prevent timeouts)
            batch_size = min(5, len(self.classification_queue))
            batch = self.classification_queue[:batch_size]
            self.classification_queue = self.classification_queue[batch_size:]
            
            logger.info(f"Processing classification batch of {len(batch)} tasks")
            
            # Classify the batch
            results = self.classification_service.classify_tasks_batch(batch)
            
            # Update tasks in the database
            updated_count = 0
            
            for task_data in batch:
                task_id = task_data['id']
                task = TaskDB.get_by_id(task_id)
                
                if task and task_id in results:
                    old_categories = task.categories.copy() if task.categories else []
                    task.categories = results[task_id]
                    
                    if task.categories != old_categories:
                        task.save()  # Save to database
                        updated_count += 1
                        logger.debug(f"Updated task '{task.title}' with categories: {task.categories}")
            
            if updated_count > 0:
                logger.info(f"Updated {updated_count} tasks with new categories")
                
            
        except Exception as e:
            logger.error(f"Error processing classification batch: {str(e)}")
        finally:
            self.is_processing = False
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Get current status of the classification queue"""
        return {
            'queue_size': len(self.classification_queue),
            'deferred_tasks_count': len(self.deferred_tasks),
            'is_processing': self.is_processing,
            'ollama_available': self.classification_service.is_ollama_available()
        }
    
    
    def clear_queue(self):
        """Clear the classification queue"""
        self.classification_queue.clear()
        self.deferred_tasks.clear()
        logger.info("Classification queue and deferred tasks cleared")

    def cancel_deferred_task(self, task_id: int) -> bool:
        """Cancel a deferred task if it exists"""
        if task_id in self.deferred_tasks:
            del self.deferred_tasks[task_id]
            logger.debug(f"Cancelled deferred classification for task {task_id}")
            return True
        return False
    
    def force_classify_task(self, task: TaskDB) -> List[str]:
        """
        Force immediate classification of a single task (synchronous)
        
        Args:
            task: TaskDB object to classify
            
        Returns:
            List of assigned categories
        """
        try:
            if not self.classification_service.is_ollama_available():
                logger.warning("Ollama not available for immediate classification")
                return []
            
            categories = self.classification_service.classify_task(task.title, task.description)
            
            # Update the task in database
            task.categories = categories
            task.save()
            
            logger.info(f"Force classified task '{task.title}' with categories: {categories}")
            return categories
            
        except Exception as e:
            logger.error(f"Force classification failed for task '{task.title}': {str(e)}")
            return []
