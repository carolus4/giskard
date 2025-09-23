#!/usr/bin/env python3
"""
Test script for auto-categorization feature
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.classification_service import TaskClassificationService
from utils.classification_manager import ClassificationManager
from models.task_db import TaskDB

def test_classification_service():
    """Test the classification service directly"""
    print("🧪 Testing Classification Service...")
    
    service = TaskClassificationService()
    
    # Test if Ollama is available
    if not service.is_ollama_available():
        print("❌ Ollama not available. Please start Ollama with gemma3:4b model.")
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
    
    manager = ClassificationManager()
    
    # Test startup classification
    print("📊 Running startup classification...")
    classified_count = manager.classify_on_startup()
    print(f"✅ Classified {classified_count} tasks on startup")
    
    # Test queue status
    print(f"📈 Queue length: {len(manager.classification_queue)}")
    print(f"📈 Is processing: {manager.is_processing}")

def test_task_model():
    """Test the updated TaskDB model with categories"""
    print("\n🧪 Testing TaskDB Model with Categories...")
    
    # Test creating task with categories
    task = TaskDB(title="Test task", description="Test description", categories=["health", "career"])
    print(f"✅ Created task with categories: {task.categories}")
    
    # Test saving to database
    task.save()
    print(f"✅ Saved task to database with ID: {task.id}")
    
    # Test retrieving from database
    retrieved_task = TaskDB.get_by_id(task.id)
    if retrieved_task:
        print(f"✅ Retrieved task categories: {retrieved_task.categories}")
    
    # Test task detail page data format
    task_dict = task.to_dict()
    print(f"✅ Task dict for UI: {task_dict}")
    
    # Clean up test task
    if task.id:
        from database import get_connection
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM tasks WHERE id = ?', (task.id,))
        conn.commit()
        conn.close()
        print("✅ Cleaned up test task")

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
