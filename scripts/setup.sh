#!/bin/bash

# Setup script for AI Guest Response Agent
set -e

echo "==================================="
echo "AI Guest Response Agent Setup"
echo "==================================="
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"

# Check Docker
echo "Checking Docker..."
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed. Please install Docker first."
    exit 1
fi
echo "Docker: OK"

# Check Docker Compose
echo "Checking Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    echo "Error: Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi
echo "Docker Compose: OK"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env
    echo ""
    echo "⚠️  IMPORTANT: Please edit .env and add your API keys:"
    echo "   - OPENAI_API_KEY"
    echo "   - DEEPSEEK_API_KEY"
    echo "   - LANGSMITH_API_KEY (optional)"
    echo ""
    read -p "Press Enter once you've added your API keys..."
fi

# Start Docker services
echo "Starting Docker services (Qdrant, Prometheus, Grafana)..."
docker-compose up -d qdrant prometheus grafana

echo "Waiting for services to start..."
sleep 10

# Check Qdrant
echo "Checking Qdrant..."
if curl -s http://localhost:6333/healthz > /dev/null; then
    echo "Qdrant: OK"
else
    echo "Error: Qdrant is not responding. Check Docker logs."
    exit 1
fi

# Generate synthetic data
echo ""
echo "Generating synthetic data..."
python scripts/generate_synthetic_data.py

# Setup Qdrant and index templates
echo ""
echo "Indexing templates in Qdrant..."
python scripts/setup_qdrant.py

echo ""
echo "==================================="
echo "Setup complete! 🎉"
echo "==================================="
echo ""
echo "Next steps:"
echo "1. Run the application: python src/main.py"
echo "2. View Swagger docs: http://localhost:8000/docs"
echo "3. View Grafana dashboard: http://localhost:3000 (admin/admin)"
echo "4. View Prometheus: http://localhost:9090"
echo ""
echo "To run tests: pytest"
echo "To start full stack: docker-compose up"
echo ""
