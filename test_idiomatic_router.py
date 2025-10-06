#!/usr/bin/env python3
"""
Test script for the idiomatic router implementation
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from orchestrator.orchestrator import Orchestrator
from orchestrator.config.router_config import RouterConfigManager
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_idiomatic_router():
    """Test the idiomatic router implementation"""
    try:
        # Initialize the orchestrator with configuration
        config_manager = RouterConfigManager.from_env()
        orchestrator = Orchestrator(config_manager)
        logger.info("✅ Orchestrator initialized successfully")
        
        # Test router info
        router_info = orchestrator.get_router_info()
        logger.info(f"✅ Router info: {router_info}")
        
        # Test a simple routing request
        test_input = "Create a task to review the quarterly report"
        logger.info(f"Testing with input: {test_input}")
        
        # Run the orchestrator
        result = orchestrator.run(test_input, session_id="test-session")
        
        logger.info(f"✅ Idiomatic router test completed")
        logger.info(f"Success: {result.get('success')}")
        logger.info(f"Final message: {result.get('final_message')}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Idiomatic router test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_router_configuration():
    """Test the router configuration system"""
    try:
        # Test default configuration
        config_manager = RouterConfigManager.from_env()
        logger.info("✅ Configuration manager initialized")
        
        # Test model config
        model_config = config_manager.get_model_config()
        logger.info(f"✅ Model config: {model_config}")
        
        # Test API config
        api_config = config_manager.get_api_config()
        logger.info(f"✅ API config: {api_config}")
        
        # Test router config
        router_config = config_manager.get_router_config()
        logger.info(f"✅ Router config: {router_config}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Configuration test failed: {str(e)}")
        return False

def test_router_chain():
    """Test the router chain directly"""
    try:
        from orchestrator.tools.router import Router
        
        # Initialize router
        router = Router()
        logger.info("✅ Router initialized")
        
        # Test available tools
        tools = router.get_available_tools()
        logger.info(f"✅ Available tools: {tools}")
        
        # Test tool descriptions
        descriptions = router.get_tool_descriptions()
        logger.info(f"✅ Tool descriptions: {descriptions[:100]}...")
        
        # Test router chain
        test_input = "What are my current tasks?"
        decision = router.plan_actions(test_input)
        logger.info(f"✅ Router decision: {decision}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Router chain test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 Testing Idiomatic Router Implementation")
    print("=" * 50)
    
    # Test configuration
    print("\n1. Testing Configuration System...")
    config_success = test_router_configuration()
    print(f"Configuration test: {'✅ PASSED' if config_success else '❌ FAILED'}")
    
    # Test router chain
    print("\n2. Testing Router Chain...")
    chain_success = test_router_chain()
    print(f"Router chain test: {'✅ PASSED' if chain_success else '❌ FAILED'}")
    
    # Test full orchestrator
    print("\n3. Testing Full Orchestrator...")
    orchestrator_success = test_idiomatic_router()
    print(f"Orchestrator test: {'✅ PASSED' if orchestrator_success else '❌ FAILED'}")
    
    # Summary
    print("\n" + "=" * 50)
    all_tests_passed = config_success and chain_success and orchestrator_success
    print(f"Overall result: {'✅ ALL TESTS PASSED' if all_tests_passed else '❌ SOME TESTS FAILED'}")
    
    if not all_tests_passed:
        sys.exit(1)
