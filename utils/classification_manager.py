"""
Classification manager for handling task categorization queue and startup classification
"""
import asyncio
import threading
import time
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from models.task import Task, TaskCollection
from utils.classification_service import TaskClassificationService
from utils.file_manager import TodoFileManager

logger = logging.getLogger(__name__)

class ClassificationManager:
    """Manages task classification queue and background processing"""
    
    def __init__(self, file_manager: TodoFileManager):
        self.file_manager = file_manager
        self.classification_service = TaskClassificationService()
        self.classification_queue = []
        self.is_processing = False
        self.processing_thread = None
        self.stop_event = threading.Event()
        
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
            
            collection = self.file_manager.load_tasks()
            uncategorized_tasks = [task for task in collection.tasks if not task.categories]
            
            if not uncategorized_tasks:
                logger.info("No uncategorized tasks found")
                return 0
            
            logger.info(f"Found {len(uncategorized_tasks)} uncategorized tasks, starting classification...")
            
            # Prepare tasks for batch classification
            task_data = []
            for task in uncategorized_tasks:
                task_data.append({
                    'file_idx': task.file_idx,
                    'title': task.title,
                    'description': task.description
                })
            
            # Classify in batch
            results = self.classification_service.classify_tasks_batch(task_data)
            
            # Update tasks with categories
            updated_count = 0
            for task in uncategorized_tasks:
                if task.file_idx in results:
                    task.categories = results[task.file_idx]
                    if task.categories:  # Only count if categories were assigned
                        updated_count += 1
            
            # Save updated tasks
            if updated_count > 0:
                self.file_manager.save_tasks(collection)
                logger.info(f"Classified {updated_count} tasks on startup")
            
            return updated_count
            
        except Exception as e:
            logger.error(f"Startup classification failed: {str(e)}")
            return 0
    
    def enqueue_classification(self, task: Task):
        """
        Add a task to the classification queue
        
        Args:
            task: Task object to classify
        """
        # Always enqueue for classification - even if task already has categories
        # This allows re-classification when task content is updated
        self.classification_queue.append({
            'file_idx': task.file_idx,
            'title': task.title,
            'description': task.description,
            'timestamp': datetime.now()
        })
        logger.debug(f"Enqueued task for classification: {task.title}")
    
    def enqueue_tasks_batch(self, tasks: List[Task]):
        """
        Add multiple tasks to the classification queue
        
        Args:
            tasks: List of Task objects to classify
        """
        for task in tasks:
            self.enqueue_classification(task)
    
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
            
            # Update tasks in the file
            collection = self.file_manager.load_tasks()
            updated_count = 0
            
            for task_data in batch:
                file_idx = task_data['file_idx']
                task = collection.get_task_by_file_idx(file_idx)
                
                if task and file_idx in results:
                    old_categories = task.categories.copy()
                    task.categories = results[file_idx]
                    
                    if task.categories != old_categories:
                        updated_count += 1
                        logger.debug(f"Updated task '{task.title}' with categories: {task.categories}")
            
            # Save if any tasks were updated
            if updated_count > 0:
                self.file_manager.save_tasks(collection)
                logger.info(f"Updated {updated_count} tasks with new categories")
                
            
        except Exception as e:
            logger.error(f"Error processing classification batch: {str(e)}")
        finally:
            self.is_processing = False
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Get current status of the classification queue"""
        return {
            'queue_size': len(self.classification_queue),
            'is_processing': self.is_processing,
            'ollama_available': self.classification_service.is_ollama_available()
        }
    
    
    def clear_queue(self):
        """Clear the classification queue"""
        self.classification_queue.clear()
        logger.info("Classification queue cleared")
    
    def force_classify_task(self, task: Task) -> List[str]:
        """
        Force immediate classification of a single task (synchronous)
        
        Args:
            task: Task to classify
            
        Returns:
            List of assigned categories
        """
        try:
            if not self.classification_service.is_ollama_available():
                logger.warning("Ollama not available for immediate classification")
                return []
            
            categories = self.classification_service.classify_task(task.title, task.description)
            
            # Update the task
            task.categories = categories
            
            # Save to file
            collection = self.file_manager.load_tasks()
            file_task = collection.get_task_by_file_idx(task.file_idx)
            if file_task:
                file_task.categories = categories
                self.file_manager.save_tasks(collection)
            
            logger.info(f"Force classified task '{task.title}' with categories: {categories}")
            return categories
            
        except Exception as e:
            logger.error(f"Force classification failed for task '{task.title}': {str(e)}")
            return []
