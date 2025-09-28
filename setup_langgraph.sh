#!/bin/bash
# Setup script for LangGraph migration

echo "🚀 Setting up LangGraph for Giskard Agent"
echo "========================================"

# Install dependencies
echo "📦 Installing LangGraph dependencies..."
pip install -r requirements.txt

# Install LangGraph CLI with inmem extras for local development
echo "🔧 Installing LangGraph CLI..."
pip install -U "langgraph-cli[inmem]"

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cat > .env << EOF
# LangGraph configuration
LANGGRAPH_API_KEY=your_api_key_here
LANGGRAPH_TENANT_ID=your_tenant_id_here

# Ollama configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma3:4b
EOF
    echo "✅ Created .env file - please update with your actual API keys"
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "1. Update .env with your API keys (optional for local development)"
echo "2. Test the LangGraph agent: python test_langgraph_agent.py"
echo "3. Start LangGraph Studio: langgraph dev"
echo "4. Start the Flask app: python app.py"
echo ""
echo "New API endpoints:"
echo "- POST /api/agent/langgraph/step (LangGraph agent)"
echo "- GET /api/agent/langgraph/graph/visualize (Graph visualization)"
echo ""
echo "LangGraph Studio will open in your browser for visual debugging!"
