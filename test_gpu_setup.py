#!/usr/bin/env python3
"""
Test script to verify GPU setup and model status
"""

import subprocess
import requests
import time
import os

def check_ollama_running():
    """Check if Ollama is running"""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        return response.status_code == 200
    except:
        return False

def check_model_running(model_name):
    """Check if a specific model is running"""
    try:
        result = subprocess.run(['ollama', 'ps'], capture_output=True, text=True)
        return model_name in result.stdout
    except:
        return False

def check_model_gpu(model_name):
    """Check if a model is using GPU"""
    try:
        result = subprocess.run(['ollama', 'ps'], capture_output=True, text=True)
        return f"{model_name}" in result.stdout and "gpu" in result.stdout.lower()
    except:
        return False

def test_gpu_setup():
    """Test the GPU setup"""
    print("🧪 Testing GPU Setup for Giskard")
    print("=" * 40)
    
    # Check if Ollama is running
    if check_ollama_running():
        print("✅ Ollama is running")
    else:
        print("❌ Ollama is not running")
        return False
    
    # Check target model
    target_model = "llama3.1:8b"
    print(f"\n🔍 Checking {target_model}:")
    
    if check_model_running(target_model):
        print(f"✅ {target_model} is running")
        
        if check_model_gpu(target_model):
            print(f"🚀 {target_model} is using GPU - Excellent!")
            return True
        else:
            print(f"⚠️  {target_model} is running but NOT using GPU")
            return False
    else:
        print(f"❌ {target_model} is not running")
        return False

if __name__ == "__main__":
    success = test_gpu_setup()
    if success:
        print("\n🎉 GPU setup test passed!")
    else:
        print("\n❌ GPU setup test failed!")
        print("💡 Try running the updated start_giskard.sh script")
