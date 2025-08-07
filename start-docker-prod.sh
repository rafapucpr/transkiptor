#!/bin/bash

echo "🚀 Iniciando Transkiptor em PRODUÇÃO com Docker Compose..."
echo "📝 Frontend: http://localhost"
echo "🚀 Backend API: http://localhost:8000"
echo "📖 Documentação: http://localhost:8000/docs"
echo ""

# Build and start containers in production mode
docker-compose -f docker-compose.prod.yml up --build -d

echo "✅ Containers iniciados em modo daemon"
echo "📊 Para ver logs: docker-compose -f docker-compose.prod.yml logs -f"
echo "🛑 Para parar: docker-compose -f docker-compose.prod.yml down"