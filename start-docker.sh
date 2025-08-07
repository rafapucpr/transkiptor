#!/bin/bash

echo "🐳 Iniciando Transkiptor com Docker Compose..."
echo "📝 Frontend: http://localhost"
echo "🚀 Backend API: http://localhost:8000"
echo "📖 Documentação: http://localhost:8000/docs"
echo ""

# Build and start containers
docker-compose up --build