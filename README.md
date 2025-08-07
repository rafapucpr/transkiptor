# Transkiptor

🎬 **Sistema completo de transcrição e download de vídeos do YouTube**

API para transcrição de áudio e download de vídeos do YouTube usando yt-dlp, whisper.cpp e OpenAI Whisper.

## ✨ Funcionalidades

### 🎤 **Transcrição de Áudio**
- Transcrição usando **whisper.cpp (C++)** como primeira opção
- Fallback para **OpenAI Whisper CLI** e **Python library**
- Suporte a detecção automática de idioma
- Transcrição em português por padrão

### 📺 **Download de Vídeos**  
- Download de vídeos em **alta qualidade (1080p)**
- Formato MP4 otimizado
- Nome de arquivo automático baseado no título

### 🛠️ **Recursos Técnicos**
- API REST com FastAPI
- Interface web moderna
- Docker e Docker Compose prontos para produção
- FFmpeg local integrado
- Limpeza automática de arquivos temporários

## 🏗️ Estrutura do Projeto

```
transkiptor/
├── 📄 README.md                    # Documentação
├── 🐳 docker-compose.yml           # Desenvolvimento
├── 🚀 docker-compose.prod.yml     # Produção
├── 🗄️  backend/                     # API Backend
│   ├── main.py                     # FastAPI application
│   ├── Dockerfile                  # Container desenvolvimento
│   ├── Dockerfile.prod             # Container produção
│   ├── requirements.txt            # Dependências Python
│   ├── models/                     # Schemas Pydantic
│   ├── routes/                     # Endpoints da API
│   ├── services/                   # Lógica de negócio
│   └── 🛠️  tools/                   # Binários (FFmpeg + whisper.cpp)
└── 🌐 frontend/                     # Interface Web
    ├── index.html                  # Interface principal
    ├── script.js                   # Lógica JavaScript
    ├── styles.css                  # Estilos CSS
    ├── Dockerfile                  # Container nginx
    └── nginx.conf                  # Configuração nginx
```

## 🚀 Execução com Docker (Recomendado)

### **Desenvolvimento**
```bash
# Clonar repositório
git clone <repository-url>
cd transkiptor

# Iniciar com Docker Compose
./start-docker.sh
```

### **Produção**
```bash
# Iniciar em modo produção (daemon)
./start-docker-prod.sh

# Ver logs
docker-compose -f docker-compose.prod.yml logs -f

# Parar containers
docker-compose -f docker-compose.prod.yml down
```

### **Acessos:**
- 🌐 **Frontend:** http://localhost
- 🚀 **Backend API:** http://localhost:8000  
- 📖 **Documentação:** http://localhost:8000/docs

## 🐳 Comandos Docker Úteis

```bash
# Build e start
docker-compose up --build

# Background/daemon mode
docker-compose up -d

# Ver logs
docker-compose logs -f

# Parar containers
docker-compose down

# Remover volumes
docker-compose down -v

# Produção
docker-compose -f docker-compose.prod.yml up -d
```

## 🛠️ Execução Manual (Sem Docker)

### **Pré-requisitos**
- Python 3.12+
- Docker e Docker Compose

### **Instalação**
```bash
# 1. Instalar dependências do sistema
sudo apt update
sudo apt install -y docker.io docker-compose-plugin

# 2. Clonar repositório
git clone <repository-url>
cd transkiptor

# 3. Executar
./start-docker.sh
```

## 📡 Endpoints da API

### **POST** `/api/v1/transcribe`
Transcreve áudio de vídeo do YouTube

**Request:**
```json
{
  "url": "https://www.youtube.com/watch?v=VIDEO_ID",
  "language": "pt"  // opcional, padrão: "auto"
}
```

**Response:**
```json
{
  "transcription": "Texto transcrito do áudio...",
  "duration": 120.5,
  "language": "pt",
  "success": true
}
```

### **POST** `/api/v1/download`
Baixa vídeo do YouTube em alta qualidade

**Request:**
```json
{
  "url": "https://www.youtube.com/watch?v=VIDEO_ID"
}
```

**Response:** Arquivo de vídeo (.mp4)

### **GET** `/`
Status da API e informações

## 🌐 Interface Web

A interface web oferece:
- ✅ Campo para URL do YouTube
- ✅ Seleção de idioma (português padrão)
- ✅ Botão **"📺 Baixar Vídeo"** (1080p)
- ✅ Botão **"Baixar Transcrição"** 
- ✅ Visualização do resultado
- ✅ Download de arquivos .txt
- ✅ Cópia para clipboard

## 🎯 Hierarquia de Transcrição

1. **🥇 whisper.cpp** (C++ - alta performance)
2. **🥈 OpenAI Whisper CLI** (fallback)  
3. **🥉 OpenAI Whisper Python** (último recurso)

## ⚙️ Configuração

### **Variáveis de Ambiente** (`.env`)
```bash
# Aplicação
ENV=development
DEBUG=true
API_HOST=0.0.0.0
API_PORT=8000

# Produção
WORKERS=4
LOG_LEVEL=INFO
```

### **Qualidade de Vídeo**
- Prioriza **1080p** quando disponível
- Fallback automático para resoluções menores
- Formato MP4 otimizado

## 🔧 Solução de Problemas

### **Containers não iniciam**
```bash
# Verificar Docker
docker --version
docker-compose --version

# Logs detalhados
docker-compose logs backend
docker-compose logs frontend
```

### **Erro de permissões**
```bash
# Dar permissões aos scripts
chmod +x start-docker.sh start-docker-prod.sh
```

### **Problemas de download**
- Verificar se a URL do YouTube é válida
- Alguns vídeos podem ter restrições geográficas
- Vídeos privados não são suportados

## 🚀 Deploy em Produção

1. **Configurar ambiente:**
```bash
cp .env.example .env
# Editar configurações de produção
```

2. **Iniciar em produção:**
```bash
./start-docker-prod.sh
```

3. **Configurar nginx/proxy reverso** (opcional)

4. **Monitoramento:**
```bash
docker-compose -f docker-compose.prod.yml logs -f
```

## 📋 Exemplo de Uso (cURL)

```bash
# Transcrição
curl -X POST "http://localhost:8000/api/v1/transcribe" \
     -H "Content-Type: application/json" \
     -d '{
       "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
       "language": "pt"
     }'

# Download de vídeo
curl -X POST "http://localhost:8000/api/v1/download" \
     -H "Content-Type: application/json" \
     -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}' \
     --output video.mp4
```

## 🛡️ Segurança

- Containers executam com usuário não-root
- Arquivos temporários são limpos automaticamente
- Rate limiting pode ser adicionado se necessário
- CORS configurado para desenvolvimento

## 📈 Performance

- **Produção:** 4 workers uvicorn
- **Cache:** Nginx para arquivos estáticos
- **Compressão:** Gzip habilitado
- **Health checks:** Monitoramento automático

---

**Desenvolvido com ❤️ usando FastAPI, Docker, whisper.cpp e yt-dlp**