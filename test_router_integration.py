#!/usr/bin/env python3
"""
Test script for the merged router functionality
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from orchestrator.langgraph_orchestrator import LangGraphOrchestrator
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_router_integration():
    """Test the router integration"""
    try:
        # Initialize the orchestrator
        orchestrator = LangGraphOrchestrator()
        logger.info("✅ Orchestrator initialized successfully")
        
        # Test a simple routing request
        test_input = "Create a task to review the quarterly report"
        logger.info(f"Testing with input: {test_input}")
        
        # Run the orchestrator
        result = orchestrator.run(test_input, session_id="test-session")
        
        logger.info(f"✅ Router integration test completed")
        logger.info(f"Success: {result.get('success')}")
        logger.info(f"Final message: {result.get('final_message')}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Router integration test failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_router_integration()
    if success:
        print("✅ Router integration test passed!")
    else:
        print("❌ Router integration test failed!")
        sys.exit(1)
