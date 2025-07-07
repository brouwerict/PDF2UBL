#!/bin/bash
# Quick PDF2UBL Update - Your current script improved
echo "🔄 Updating PDF2UBL..."
cd ~/PDF2UBL

echo "📥 Pulling latest code..."
git pull

echo "🛑 Stopping container..."
sudo docker stop pdf2ubl 2>/dev/null || true
sudo docker rm pdf2ubl 2>/dev/null || true

echo "🏗️ Building new image..."
sudo docker build -t pdf2ubl .

echo "🚀 Starting new container..."
sudo docker run -d --name pdf2ubl -p 8000:8000 --restart unless-stopped pdf2ubl

echo "✅ Update complete!"
sudo docker ps | grep pdf2ubl
sudo docker logs --tail 10 pdf2ubl