#!/bin/bash

# Exit on error
set -e

echo "🚀 Starting deployment process..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if docker-compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "ℹ️ .env file not found. Creating from .env.example..."
    cp .env.example .env
    echo "⚠️ Please update the .env file with your configuration and run this script again."
    exit 1
fi

# Load environment variables
echo "🔧 Loading environment variables..."
set -a
source .env
set +a

# Build and start containers
echo "🚢 Building and starting containers..."
docker-compose -f docker-compose.yml up -d --build

# Check if the application is running
if [ $? -eq 0 ]; then
    echo "✅ Deployment successful!"
    echo "🌐 Application is running on http://localhost:8000"
    echo "📚 API documentation is available at http://localhost:8000/docs"
    echo "
To view logs, run: docker-compose logs -f"
    echo "To stop the application, run: docker-compose down"
else
    echo "❌ Deployment failed. Check the logs for more information."
    exit 1
fi
