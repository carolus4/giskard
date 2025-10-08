#!/bin/bash

# Setup script for Langfuse integration with Giskard agent

echo "🚀 Setting up Langfuse integration for Giskard agent"
echo "=================================================="

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

# Install Langfuse and python-dotenv
echo "📦 Installing Langfuse SDK and dependencies..."
pip install langfuse>=3.0.0 python-dotenv>=1.0.0

if [ $? -eq 0 ]; then
    echo "✅ Langfuse SDK installed successfully"
else
    echo "❌ Failed to install Langfuse SDK"
    exit 1
fi

# Check for environment variables (including .env file)
echo ""
echo "🔧 Checking Langfuse configuration..."

# Load .env file if it exists
if [ -f ".env" ]; then
    echo "📄 Loading .env file..."
    export $(grep -v '^#' .env | xargs)
fi

if [ -z "$LANGFUSE_PUBLIC_KEY" ] || [ -z "$LANGFUSE_SECRET_KEY" ]; then
    echo "⚠️  Langfuse environment variables not set"
    echo ""
    echo "To set up Langfuse, you have two options:"
    echo ""
    echo "Option 1: Use a .env file (Recommended)"
    echo "1. Copy the example file: cp env.example .env"
    echo "2. Edit .env with your API keys from https://cloud.langfuse.com"
    echo "3. Run this script again"
    echo ""
    echo "Option 2: Set environment variables"
    echo "1. Go to https://cloud.langfuse.com"
    echo "2. Create an account or sign in"
    echo "3. Go to Settings > API Keys"
    echo "4. Create a new API key"
    echo "5. Set the environment variables:"
    echo ""
    echo "   export LANGFUSE_PUBLIC_KEY='your-public-key'"
    echo "   export LANGFUSE_SECRET_KEY='your-secret-key'"
    echo ""
    echo "   # Optional: Set custom host (defaults to https://cloud.langfuse.com)"
    echo "   export LANGFUSE_HOST='https://cloud.langfuse.com'"
    echo ""
    echo "6. Add these to your ~/.bashrc or ~/.zshrc for persistence"
    echo ""
    echo "Then run this script again to test the integration."
    exit 1
else
    echo "✅ Langfuse environment variables are set"
    if [ -f ".env" ]; then
        echo "   Source: .env file"
    else
        echo "   Source: environment variables"
    fi
    echo "   Public Key: ${LANGFUSE_PUBLIC_KEY:0:10}..."
    echo "   Host: ${LANGFUSE_HOST:-https://cloud.langfuse.com}"
fi

# Test the integration
echo ""
echo "🧪 Testing Langfuse integration..."
python3 test_langfuse_integration.py

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 Langfuse integration is ready!"
    echo ""
    echo "📝 What's been set up:"
    echo "✅ Langfuse SDK installed"
    echo "✅ Environment variables configured"
    echo "✅ Integration tested successfully"
    echo ""
    echo "🚀 You can now run your Giskard agent and see traces in the Langfuse dashboard!"
    echo "   Dashboard: https://cloud.langfuse.com"
else
    echo ""
    echo "❌ Integration test failed. Please check the error messages above."
    exit 1
fi
