#!/bin/bash
# IFP Edge - Quick Start Script

set -e  # Exit on error

echo "🚀 Starting IFP Edge..."
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    echo "   Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose is not installed."
    exit 1
fi

# Create .env if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
fi

# Clean up any existing containers
echo "🧹 Cleaning up any existing IFP Edge containers..."
docker compose down 2>/dev/null || true

# Start services
echo "🐳 Starting Docker services..."
docker compose up -d --build

# Wait for services to be ready
echo ""
echo "⏳ Waiting for services to start..."
sleep 10

# Check service health
echo ""
echo "🔍 Checking service health..."
docker compose ps

echo ""
echo "✅ IFP Edge is running!"
echo ""
echo "Access your dashboards:"
echo "  📊 Grafana:    http://localhost:3003 (admin/admin)"
echo "  📈 Prometheus: http://localhost:9091"
echo "  🌐 Demo App:   http://localhost:8081"
echo "  💰 O2 Wallet:  http://localhost:8086/docs"
echo ""
echo "Note: Using alternative ports to avoid conflicts with main IFP deployment"
echo ""
echo "To view logs:"
echo "  docker compose logs -f"
echo ""
echo "To stop:"
echo "  docker compose down"
echo ""
