#!/bin/bash
# Docker Compose Update Script
echo "🔄 Updating PDF2UBL with Docker Compose..."
cd ~/PDF2UBL

echo "📥 Pulling latest code..."
git pull

echo "🛑 Stopping services..."
sudo docker-compose down

echo "🏗️ Building and starting..."
sudo docker-compose up -d --build

echo "✅ Update complete!"
sudo docker-compose ps
sudo docker-compose logs --tail 10