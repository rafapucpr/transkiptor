#!/bin/bash

# Script para configurar diretório /home/appuser com permissões corretas

echo "🔧 Configurando diretório /home/appuser para container..."

# Criar diretório se não existir
sudo mkdir -p /home/appuser

# Definir propriedade para o usuário do container (UID 1000, GID 1000)
# Isso corresponde ao usuário 'appuser' criado no Dockerfile
sudo chown 1000:1000 /home/appuser

# Definir permissões adequadas
sudo chmod 755 /home/appuser

echo "✅ Diretório /home/appuser configurado com sucesso!"
echo "   - Proprietário: appuser (1000:1000)"
echo "   - Permissões: 755"

# Verificar configuração
ls -la /home/appuser/..  | grep appuser