#!/usr/bin/env python3
"""
Test script for auto-categorization feature
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.classification_service import TaskClassificationService
from utils.classification_manager import ClassificationManager
from utils.file_manager import TodoFileManager
from models.task import Task

def test_classification_service():
    """Test the classification service directly"""
    print("🧪 Testing Classification Service...")
    
    service = TaskClassificationService()
    
    # Test if Ollama is available
    if not service.is_ollama_available():
        print("❌ Ollama not available. Please start Ollama with llama3.1:8b model.")
        return False
    
    print("✅ Ollama is available")
    
    # Test classification
    test_tasks = [
        ("Go to the gym", "Work out for 30 minutes"),
        ("Complete Python certification", "Finish the online course"),
        ("Read a book about productivity", "Learn new techniques"),
        ("Buy groceries", "Get milk and bread"),
        ("Prepare for job interview", "Review common questions"),
        ("Take vitamins", "Daily health routine")
    ]
    
    print("\n📝 Testing task classification:")
    for title, description in test_tasks:
        categories = service.classify_task(title, description)
        print(f"  '{title}' -> {categories}")

def test_classification_manager():
    """Test the classification manager"""
    print("\n🧪 Testing Classification Manager...")
    
    file_manager = TodoFileManager()
    manager = ClassificationManager(file_manager)
    
    # Test startup classification
    print("📊 Running startup classification...")
    classified_count = manager.classify_on_startup()
    print(f"✅ Classified {classified_count} tasks on startup")
    
    # Test queue status
    status = manager.get_queue_status()
    print(f"📈 Queue status: {status}")

def test_task_model():
    """Test the updated Task model with categories"""
    print("\n🧪 Testing Task Model with Categories...")
    
    # Test creating task with categories
    task = Task("Test task", "Test description", categories=["health", "career"])
    print(f"✅ Created task with categories: {task.categories}")
    
    # Test to_line format
    line = task.to_line()
    print(f"✅ Task line format: {line}")
    
    # Test parsing back
    parsed_task = Task.from_line(line, 0)
    print(f"✅ Parsed task categories: {parsed_task.categories}")
    
    # Test task detail page data format
    task_dict = task.to_dict(ui_id=1)
    print(f"✅ Task dict for UI: {task_dict}")

def test_frontend_categories():
    """Test frontend category display"""
    print("\n🧪 Testing Frontend Category Display...")
    
    # Test different category combinations
    test_cases = [
        (["health"], "Health task"),
        (["career", "learning"], "Professional development"),
        (["health", "career", "learning"], "Complete wellness program"),
        ([], "Generic task")
    ]
    
    for categories, title in test_cases:
        task = Task(title, "Test description", categories=categories)
        task_dict = task.to_dict(ui_id=1)
        print(f"  '{title}' -> {task_dict['categories']}")

if __name__ == "__main__":
    print("🚀 Testing Auto-Categorization Feature\n")
    
    try:
        test_task_model()
        test_frontend_categories()
        test_classification_service()
        test_classification_manager()
        print("\n✅ All tests completed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
