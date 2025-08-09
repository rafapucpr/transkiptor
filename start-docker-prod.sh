#!/bin/bash

echo "🚀 Iniciando Transkiptor em PRODUÇÃO com Docker Compose..."
echo "📝 Frontend: http://localhost"
echo "🚀 Backend API: http://localhost:8000"
echo "📖 Documentação: http://localhost:8000/docs"
echo ""

# Configure appuser directory permissions if needed
echo "🔧 Configurando permissões do diretório appuser..."
if [ -f "./setup-appuser-dir.sh" ]; then
    echo "ℹ️ Execute manualmente se necessário: sudo ./setup-appuser-dir.sh"
fi

# Build and start containers in production mode
docker-compose -f docker-compose.prod.yml up --build -d

echo "✅ Containers iniciados em modo daemon"
echo "📊 Para ver logs: docker-compose -f docker-compose.prod.yml logs -f"
echo "🛑 Para parar: docker-compose -f docker-compose.prod.yml down"