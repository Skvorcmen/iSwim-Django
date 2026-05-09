#!/bin/bash
echo "🚀 Installing system dependencies..."
apt-get update && apt-get install -y libpq-dev gcc python3-dev

echo "🚀 Installing Python packages..."
pip install --upgrade pip
pip install -r requirements.txt

echo "📦 Collecting static files..."
python manage.py collectstatic --noinput

echo "🗄️ Running migrations..."
python manage.py migrate

echo "✅ Build completed!"
