#!/usr/bin/env python3
"""
Test script for classification with Langfuse tracing
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.classification_service import TaskClassificationService
from utils.classification_manager import ClassificationManager
from config.langfuse_config import langfuse_config
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_single_classification_with_trace():
    """Test single task classification with Langfuse tracing"""
    print("🧪 Testing Single Task Classification with Langfuse Tracing...")

    service = TaskClassificationService()

    # Test if Ollama is available
    if not service.is_ollama_available():
        print("❌ Ollama not available. Please start Ollama with gemma3:4b model.")
        return False

    print("✅ Ollama is available")

    # Check if Langfuse is enabled
    if not langfuse_config.enabled:
        print("⚠️  Langfuse is not configured. Set LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY in .env")
        print("    Continuing test without Langfuse tracing...")
        trace = None
    else:
        print("✅ Langfuse is enabled")

        # Create a trace for classification
        try:
            trace = langfuse_config.client.trace(
                name="classification.test",
                input={
                    "test_type": "single_task",
                    "task_title": "Go to the gym"
                },
                metadata={
                    "test_run": True
                }
            )
            print("✅ Created Langfuse trace")
        except Exception as e:
            print(f"❌ Failed to create trace: {e}")
            trace = None

    # Test classification with trace
    test_task = {
        "title": "Go to the gym",
        "description": "Work out for 30 minutes",
        "project": "Health"
    }

    print(f"\n📝 Classifying task: '{test_task['title']}'")
    categories = service.classify_task(
        test_task['title'],
        test_task['description'],
        test_task['project'],
        trace_context=trace
    )
    print(f"   Result: {categories}")

    # Finalize the trace
    if trace:
        try:
            trace.update(output={"categories": categories})
            print("✅ Finalized Langfuse trace")
        except Exception as e:
            print(f"⚠️  Failed to finalize trace: {e}")

    # Flush Langfuse events
    if langfuse_config.enabled:
        try:
            langfuse_config.flush()
            print("✅ Flushed Langfuse events")
        except Exception as e:
            print(f"⚠️  Failed to flush events: {e}")

    print(f"\n✅ Classification completed!")
    return True


def test_batch_classification_with_trace():
    """Test batch classification with Langfuse tracing"""
    print("\n🧪 Testing Batch Classification with Langfuse Tracing...")

    manager = ClassificationManager()

    # Test if Ollama is available
    if not manager.classification_service.is_ollama_available():
        print("❌ Ollama not available. Please start Ollama with gemma3:4b model.")
        return False

    print("✅ Ollama is available")

    # Check if Langfuse is enabled
    if not langfuse_config.enabled:
        print("⚠️  Langfuse is not configured.")
        print("    Continuing test without Langfuse tracing...")
        trace = None
    else:
        print("✅ Langfuse is enabled")

    # Test batch classification
    test_tasks = [
        {
            "id": 1,
            "title": "Go to the gym",
            "description": "Work out for 30 minutes",
            "project": "Health"
        },
        {
            "id": 2,
            "title": "Complete Python certification",
            "description": "Finish the online course",
            "project": "Learning"
        },
        {
            "id": 3,
            "title": "Prepare for job interview",
            "description": "Review common questions",
            "project": "Career"
        }
    ]

    # Create trace for batch
    if langfuse_config.enabled:
        try:
            trace = langfuse_config.client.trace(
                name="classification.test_batch",
                input={
                    "test_type": "batch",
                    "batch_size": len(test_tasks),
                    "task_titles": [t['title'] for t in test_tasks]
                },
                metadata={
                    "test_run": True
                }
            )
            print("✅ Created Langfuse trace for batch")
        except Exception as e:
            print(f"❌ Failed to create trace: {e}")
            trace = None
    else:
        trace = None

    print(f"\n📝 Classifying {len(test_tasks)} tasks:")
    results = manager.classification_service.classify_tasks_batch(test_tasks, trace)

    for task in test_tasks:
        categories = results.get(task['id'], [])
        print(f"   '{task['title']}' -> {categories}")

    # Finalize the trace
    if trace:
        try:
            trace.update(output={"results": results})
            print("✅ Finalized Langfuse trace")
        except Exception as e:
            print(f"⚠️  Failed to finalize trace: {e}")

    # Flush Langfuse events
    if langfuse_config.enabled:
        try:
            langfuse_config.flush()
            print("✅ Flushed Langfuse events")
        except Exception as e:
            print(f"⚠️  Failed to flush events: {e}")

    print(f"\n✅ Batch classification completed!")
    return True


if __name__ == "__main__":
    print("🚀 Testing Classification with Langfuse Tracing\n")

    try:
        # Test single classification with trace
        test_single_classification_with_trace()

        # Test batch classification with trace
        test_batch_classification_with_trace()

        print("\n✅ All Langfuse tracing tests completed!")
        print("\n📊 Check your Langfuse dashboard to see the traces:")
        print(f"   {langfuse_config.host if langfuse_config.enabled else 'https://cloud.langfuse.com'}")

    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
