#!/usr/bin/env python3
"""
Test script to verify .env file loading for Langfuse configuration
"""
import os
import sys
from dotenv import load_dotenv

# Load .env file
load_dotenv()

print("🔧 Testing .env file loading...")
print("=" * 40)

# Check if .env file exists
if os.path.exists('.env'):
    print("✅ .env file found")
    
    # Read and display (masked) values
    with open('.env', 'r') as f:
        lines = f.readlines()
    
    print(f"📄 .env file contains {len(lines)} lines")
    
    # Check for Langfuse variables
    langfuse_vars = []
    for line in lines:
        if line.strip().startswith('LANGFUSE_'):
            var_name = line.split('=')[0]
            langfuse_vars.append(var_name)
    
    print(f"🔑 Found Langfuse variables: {', '.join(langfuse_vars)}")
    
else:
    print("⚠️  .env file not found")
    print("   Create one by copying: cp env.example .env")

print("\n🌍 Environment variables loaded:")
print(f"   LANGFUSE_PUBLIC_KEY: {'✅ Set' if os.getenv('LANGFUSE_PUBLIC_KEY') else '❌ Not set'}")
print(f"   LANGFUSE_SECRET_KEY: {'✅ Set' if os.getenv('LANGFUSE_SECRET_KEY') else '❌ Not set'}")
print(f"   LANGFUSE_HOST: {os.getenv('LANGFUSE_HOST', 'Not set (will use default)')}")

# Test Langfuse config loading
try:
    from config.langfuse_config import langfuse_config
    print(f"\n🤖 Langfuse config status:")
    print(f"   Enabled: {'✅ Yes' if langfuse_config.enabled else '❌ No'}")
    if langfuse_config.enabled:
        print(f"   Host: {langfuse_config.host}")
        print(f"   Public Key: {langfuse_config.public_key[:10]}...")
except ImportError as e:
    print(f"\n❌ Failed to import Langfuse config: {e}")
except Exception as e:
    print(f"\n❌ Error loading Langfuse config: {e}")

print("\n" + "=" * 40)
print("📝 Next steps:")
print("1. If .env file is missing: cp env.example .env")
print("2. Edit .env with your Langfuse API keys")
print("3. Run: python test_langfuse_integration.py")
