#!/bin/bash
# PDF2UBL Update Script
set -e  # Exit on any error

echo "🔄 Updating PDF2UBL..."

# Check if we're in the right directory
if [ ! -f "Dockerfile" ]; then
    echo "❌ Error: Not in PDF2UBL directory. Please cd to the project root."
    exit 1
fi

echo "📥 Pulling latest code..."
git pull

# Check if there are any changes
if [ $? -ne 0 ]; then
    echo "❌ Git pull failed. Please check your repository status."
    exit 1
fi

echo "🛑 Stopping existing container..."
sudo docker stop pdf2ubl 2>/dev/null || echo "ℹ️ No running container found"
sudo docker rm pdf2ubl 2>/dev/null || echo "ℹ️ No container to remove"

# Remove old image to force fresh build
echo "🗑️ Removing old image..."
sudo docker rmi pdf2ubl 2>/dev/null || echo "ℹ️ No old image to remove"

echo "🏗️ Building new image..."
sudo docker build -t pdf2ubl:latest .

if [ $? -ne 0 ]; then
    echo "❌ Docker build failed!"
    exit 1
fi

echo "🚀 Starting new container..."
sudo docker run -d \
    --name pdf2ubl \
    -p 8000:8000 \
    --restart unless-stopped \
    -v /tmp/pdf2ubl-uploads:/tmp \
    pdf2ubl:latest

if [ $? -eq 0 ]; then
    echo "✅ Update complete!"
    echo ""
    echo "📊 Container status:"
    sudo docker ps | grep pdf2ubl
    echo ""
    echo "📋 Recent logs:"
    sleep 2  # Give container time to start
    sudo docker logs --tail 10 pdf2ubl
    echo ""
    echo "🌐 Web interface available at: http://localhost:8000"
    echo "📱 Network access at: http://$(hostname -I | awk '{print $1}'):8000"
else
    echo "❌ Failed to start container!"
    exit 1
fi