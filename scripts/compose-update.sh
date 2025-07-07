#!/bin/bash
# Docker Compose Update Script
echo "🔄 Updating PDF2UBL with Docker Compose..."

# Navigate to project root from script location
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

echo "📥 Pulling latest code..."
git pull

echo "🛑 Stopping services..."
sudo docker-compose down

echo "🏗️ Building and starting..."
sudo docker-compose up -d --build

echo "✅ Update complete!"
sudo docker-compose ps
sudo docker-compose logs --tail 10