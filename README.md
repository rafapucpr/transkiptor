# Transkiptor

🎬 **Sistema completo de transcrição para YouTube, áudios e vídeos**

API avançada para transcrição de conteúdo multimídia usando **yt-dlp**, **whisper.cpp**, **FFmpeg** e **OpenAI Whisper**.

## ✨ Funcionalidades

### 🎤 **Transcrição de YouTube**
- Transcrição direta de vídeos do YouTube via URL
- Download e extração automática de áudio
- Suporte a diversos formatos e qualidades

### 🎵 **Transcrição de Arquivos de Áudio**
- Upload de arquivos: MP3, WAV, M4A, OGG, WEBM, FLAC, AAC
- Limite de 100MB por arquivo
- Processamento otimizado com conversão automática

### 📹 **Transcrição de Arquivos de Vídeo**
- Upload de arquivos: MP4, AVI, MOV, MKV, WEBM, FLV, WMV, M4V, 3GP, OGV
- Limite de 5GB por arquivo
- Extração automática de áudio com FFmpeg
- Processamento de vídeos de alta qualidade

### 🛠️ **Recursos Técnicos**
- **Hierarquia de transcrição inteligente:** whisper.cpp → OpenAI Whisper Python
- **Múltiplos formatos de saída:** Texto simples (.txt) ou Legendas (.srt)
- **Detecção automática de idioma** ou seleção manual
- **Interface web moderna** com drag & drop
- **API REST completa** com FastAPI
- **Docker pronto para produção**

## 🏗️ Arquitetura

```
transkiptor/
├── 📄 README.md                    # Documentação completa
├── 🐳 docker-compose.yml           # Desenvolvimento
├── 🚀 docker-compose.prod.yml     # Produção
├── 🗄️  backend/                     # API Backend (FastAPI)
│   ├── main.py                     # Aplicação principal
│   ├── requirements.txt            # Dependências Python
│   ├── models/
│   │   └── schemas.py              # Modelos Pydantic
│   ├── routes/                     # Endpoints da API
│   │   ├── youtube_transcription.py # YouTube transcription
│   │   ├── audio_transcription.py   # Audio upload transcription
│   │   ├── video_transcription.py   # Video upload transcription
│   │   └── youtube_download.py      # YouTube video download
│   ├── services/                   # Lógica de negócio
│   │   ├── youtube_service.py        # YouTube processing
│   │   ├── youtube_download_service.py # YouTube download processing
│   │   ├── audio_service.py          # Audio processing
│   │   ├── video_service.py          # Video processing
│   │   └── whisper_python_service.py # Whisper integration
│   └── 🛠️  tools/                   # Binários otimizados
│       ├── ffmpeg/                 # FFmpeg local
│       └── whisper_cpp/            # whisper.cpp C++
└── 🌐 frontend/                     # Interface Web
    ├── index.html                  # Interface principal
    ├── script.js                   # Funcionalidades interativas
    ├── styles.css                  # Design responsivo
    └── server.py                   # Servidor de desenvolvimento
```

## 📡 APIs Disponíveis

### 🎬 YouTube Transcription

#### **POST** `/api/v1/transcribe-youtube`
Transcreve áudio de vídeo do YouTube

**Request:**
```json
{
  "url": "https://www.youtube.com/watch?v=VIDEO_ID",
  "language": "auto"  // opcional: "pt", "en", "es", "fr", "de", "it"
}
```

**Response:**
```json
{
  "transcription": "Texto transcrito completo do áudio...",
  "duration": 180.5,
  "language": "pt",
  "success": true
}
```

#### **POST** `/api/v1/download-youtube`
Baixa vídeo do YouTube em alta qualidade

**Request:**
```json
{
  "url": "https://www.youtube.com/watch?v=VIDEO_ID"
}
```

**Response:** Arquivo de vídeo (.mp4) como download

### 🎵 Audio Transcription

#### **POST** `/api/v1/transcribe-audio`
Transcreve arquivo de áudio enviado

**Request:** `multipart/form-data`
- `file`: Arquivo de áudio (max 100MB)
- `language`: Idioma opcional (padrão: "auto")
- `output_format`: "txt" ou "srt" (padrão: "txt")

**Response:**
```json
{
  "transcription": "Texto transcrito ou formato SRT...",
  "duration": 120.3,
  "language": "pt",
  "output_format": "txt",
  "filename": "arquivo.mp3",
  "success": true
}
```

#### **POST** `/api/v1/transcribe-audio/download`
Transcreve áudio e retorna arquivo para download

**Request:** `multipart/form-data` (mesmos parâmetros acima)

**Response:** Arquivo .txt ou .srt como download

### 📹 Video Transcription

#### **POST** `/api/v1/transcribe-video`
Transcreve áudio extraído de arquivo de vídeo

**Request:** `multipart/form-data`
- `file`: Arquivo de vídeo (max 5GB)
- `language`: Idioma opcional (padrão: "auto")
- `output_format`: "txt" ou "srt" (padrão: "txt")

**Response:**
```json
{
  "transcription": "Texto transcrito do áudio do vídeo...",
  "duration": 300.7,
  "language": "en",
  "output_format": "srt",
  "filename": "video.mp4",
  "success": true
}
```

#### **POST** `/api/v1/transcribe-video/download`
Transcreve vídeo e retorna arquivo para download

**Request:** `multipart/form-data` (mesmos parâmetros acima)

**Response:** Arquivo .txt ou .srt como download

### 🔍 Health & Status

#### **GET** `/`
Informações gerais da API

#### **GET** `/api/v1/health` (disponível em cada serviço)
Status de saúde dos serviços

## 🚀 Execução com Docker (Recomendado)

### **Desenvolvimento**
```bash
# Clonar repositório
git clone <repository-url>
cd transkiptor

# Iniciar com Docker Compose
docker-compose up --build

# Em background
docker-compose up -d
```

### **Produção**
```bash
# Iniciar em produção
docker-compose -f docker-compose.prod.yml up -d

# Monitorar logs
docker-compose -f docker-compose.prod.yml logs -f

# Parar serviços
docker-compose -f docker-compose.prod.yml down
```

### **Acessos:**
- 🌐 **Frontend:** http://localhost:3000
- 🚀 **Backend API:** http://localhost:8000  
- 📖 **Documentação Swagger:** http://localhost:8000/docs
- 🔍 **Redoc:** http://localhost:8000/redoc

## 🌐 Interface Web Completa

### 🎬 Transcrição do YouTube
- Campo para URL do YouTube
- Seleção de idioma
- Botões para download de vídeo e transcrição
- Visualização de resultados em tempo real

### 🎵 Upload de Áudio
- **Drag & Drop** ou clique para selecionar
- Formatos: MP3, WAV, M4A, OGG, WEBM, FLAC, AAC
- Limite: 100MB
- Opções: Texto simples ou legendas SRT
- Download automático da transcrição

### 📹 Upload de Vídeo
- **Drag & Drop** ou clique para selecionar
- Formatos: MP4, AVI, MOV, MKV, WEBM, FLV, WMV, M4V, 3GP, OGV
- Limite: 5GB
- Extração automática de áudio
- Opções: Texto simples ou legendas SRT

### ✨ Recursos da Interface
- Design responsivo e moderno
- Indicadores visuais de progresso
- Validação de arquivos em tempo real
- Feedback instantâneo de erros
- Preview de informações do arquivo

## 🎯 Sistema de Transcrição Inteligente

### **Hierarquia de Processamento:**
1. **🥇 whisper.cpp (C++)** - Alta performance, processamento local
2. **🥈 OpenAI Whisper Python** - Fallback robusto

### **Idiomas Suportados:**
- 🇵🇹 Português (padrão)
- 🇺🇸 English
- 🇪🇸 Español
- 🇫🇷 Français
- 🇩🇪 Deutsch
- 🇮🇹 Italiano
- 🌍 Detecção automática

### **Formatos de Saída:**
- **TXT:** Texto simples limpo
- **SRT:** Legendas com timestamps precisos

## 📋 Exemplos de Uso

### cURL - YouTube
```bash
# Transcrição de YouTube
curl -X POST "http://localhost:8000/api/v1/transcribe-youtube" \
     -H "Content-Type: application/json" \
     -d '{
       "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
       "language": "en"
     }'

# Download de vídeo
curl -X POST "http://localhost:8000/api/v1/download-youtube" \
     -H "Content-Type: application/json" \
     -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}' \
     --output video.mp4
```

### cURL - Upload de Áudio
```bash
# Transcrição de arquivo de áudio
curl -X POST "http://localhost:8000/api/v1/transcribe-audio/download" \
     -F "file=@audio.mp3" \
     -F "language=pt" \
     -F "output_format=srt" \
     --output transcricao.srt
```

### cURL - Upload de Vídeo
```bash
# Transcrição de arquivo de vídeo
curl -X POST "http://localhost:8000/api/v1/transcribe-video/download" \
     -F "file=@video.mp4" \
     -F "language=auto" \
     -F "output_format=txt" \
     --output transcricao.txt
```

### Python
```python
import requests

# YouTube Transcription
response = requests.post(
    "http://localhost:8000/api/v1/transcribe-youtube",
    json={
        "url": "https://www.youtube.com/watch?v=VIDEO_ID",
        "language": "pt"
    }
)
result = response.json()
print(result["transcription"])

# Audio Upload
with open("audio.mp3", "rb") as f:
    files = {"file": f}
    data = {"language": "en", "output_format": "srt"}
    response = requests.post(
        "http://localhost:8000/api/v1/transcribe-audio",
        files=files,
        data=data
    )
    result = response.json()
    print(result["transcription"])
```

## 🔧 Configuração e Deploy

### **Variáveis de Ambiente**
```bash
# .env
ENV=production
DEBUG=false
API_HOST=0.0.0.0
API_PORT=8000
FRONTEND_PORT=3000
WORKERS=4
LOG_LEVEL=INFO
```

### **Requisitos de Sistema**
- **Docker & Docker Compose**
- **4GB RAM** mínimo para processamento de vídeos
- **10GB espaço livre** para arquivos temporários
- **FFmpeg** (incluído no container)

## 🛡️ Segurança e Limits

### **Limites de Upload**
- **Áudio:** 100MB
- **Vídeo:** 5GB
- **Timeout:** 10 minutos por transcrição

### **Validações**
- Verificação de formato de arquivo
- Sanitização de nomes de arquivo
- Limpeza automática de arquivos temporários
- Rate limiting configurável

### **Segurança**
- Containers não-root
- CORS configurado
- Validação de entrada com Pydantic
- Logs de auditoria

## 🔧 Solução de Problemas

### **Container Issues**
```bash
# Verificar status
docker-compose ps

# Logs detalhados
docker-compose logs backend
docker-compose logs frontend

# Restart de serviços
docker-compose restart
```

### **Problemas de Upload**
- Verificar tamanhos dos arquivos
- Formatos suportados
- Espaço em disco suficiente

### **Erros de Transcrição**
- Qualidade do áudio
- Idioma correto selecionado
- Duração do arquivo

## 📈 Performance e Monitoramento

### **Otimizações**
- **Produção:** 4 workers uvicorn
- **Cache:** Nginx para assets estáticos
- **Compressão:** Gzip habilitado
- **Health checks:** Monitoramento automático

### **Métricas**
- Tempo de processamento
- Taxa de sucesso
- Uso de recursos
- Logs estruturados

## 🚀 Deploy em Produção

### **1. Preparação**
```bash
# Clone e configuração
git clone <repository-url>
cd transkiptor
cp .env.example .env
# Editar variáveis de produção
```

### **2. Deploy**
```bash
# Subir em produção
docker-compose -f docker-compose.prod.yml up -d

# Verificar saúde
curl http://localhost:8000/
curl http://localhost:3000/
```

### **3. Monitoramento**
```bash
# Logs em tempo real
docker-compose -f docker-compose.prod.yml logs -f

# Status dos containers
docker-compose -f docker-compose.prod.yml ps

# Métricas de uso
docker stats
```

---

## 📝 Changelog

### v2.0.0 (Atual)
- ✅ **Nova API de transcrição de vídeos**
- ✅ **Upload de arquivos até 5GB**
- ✅ **Interface drag & drop completa**
- ✅ **Suporte a formato SRT com timestamps**
- ✅ **Extração de áudio com FFmpeg**

### v1.0.0
- ✅ Transcrição de YouTube
- ✅ Upload de áudios
- ✅ Interface web básica
- ✅ API REST com FastAPI

---

**Desenvolvido com ❤️ usando FastAPI, Docker, whisper.cpp, FFmpeg e yt-dlp**

🔗 **Links úteis:**
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [whisper.cpp](https://github.com/ggerganov/whisper.cpp)
- [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- [Docker](https://docs.docker.com/)