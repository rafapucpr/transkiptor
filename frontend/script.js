const API_BASE_URL = 'http://localhost:8000/api/v1';

class TranskiptorUI {
    constructor() {
        this.form = document.getElementById('transcriptionForm');
        this.transcribeBtn = document.getElementById('transcribeBtn');
        this.downloadVideoBtn = document.getElementById('downloadVideoBtn');
        this.btnText = document.querySelector('.btn-text');
        this.btnLoading = document.querySelector('.btn-loading');
        this.statusMessage = document.getElementById('statusMessage');
        this.progressBar = document.getElementById('progressBar');
        this.resultContainer = document.getElementById('resultContainer');
        this.transcriptionText = document.getElementById('transcriptionText');
        this.videoDuration = document.getElementById('videoDuration');
        this.detectedLanguage = document.getElementById('detectedLanguage');
        this.downloadBtn = document.getElementById('downloadBtn');
        this.copyBtn = document.getElementById('copyBtn');

        this.initEventListeners();
    }

    initEventListeners() {
        this.form.addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleTranscription();
        });

        this.downloadVideoBtn.addEventListener('click', () => {
            this.handleVideoDownload();
        });

        this.downloadBtn.addEventListener('click', () => {
            this.downloadTranscription();
        });

        this.copyBtn.addEventListener('click', () => {
            this.copyTranscription();
        });
    }

    showStatus(message, type = 'info') {
        this.statusMessage.textContent = message;
        this.statusMessage.className = `status-message ${type}`;
        this.statusMessage.style.display = 'block';
    }

    hideStatus() {
        this.statusMessage.style.display = 'none';
    }

    showProgress() {
        this.progressBar.style.display = 'block';
    }

    hideProgress() {
        this.progressBar.style.display = 'none';
    }

    setLoading(loading) {
        if (loading) {
            this.transcribeBtn.disabled = true;
            this.btnText.style.display = 'none';
            this.btnLoading.style.display = 'flex';
        } else {
            this.transcribeBtn.disabled = false;
            this.btnText.style.display = 'block';
            this.btnLoading.style.display = 'none';
        }
    }

    setVideoLoading(loading) {
        const btnText = this.downloadVideoBtn.querySelector('.btn-text');
        const btnLoading = this.downloadVideoBtn.querySelector('.btn-loading');
        
        if (loading) {
            this.downloadVideoBtn.disabled = true;
            this.transcribeBtn.disabled = true;
            btnText.style.display = 'none';
            btnLoading.style.display = 'flex';
        } else {
            this.downloadVideoBtn.disabled = false;
            this.transcribeBtn.disabled = false;
            btnText.style.display = 'block';
            btnLoading.style.display = 'none';
        }
    }

    showResult(data) {
        this.transcriptionText.value = data.transcription;
        this.videoDuration.textContent = `Duração: ${this.formatDuration(data.duration)}`;
        this.detectedLanguage.textContent = `Idioma: ${this.getLanguageName(data.language)}`;
        this.resultContainer.style.display = 'block';
        this.resultContainer.scrollIntoView({ behavior: 'smooth' });
    }

    hideResult() {
        this.resultContainer.style.display = 'none';
    }

    formatDuration(seconds) {
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = Math.floor(seconds % 60);
        return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
    }

    getLanguageName(code) {
        const languages = {
            'pt': 'Português',
            'en': 'English',
            'es': 'Español',
            'fr': 'Français',
            'de': 'Deutsch',
            'it': 'Italiano',
            'auto': 'Detecção automática'
        };
        return languages[code] || code;
    }

    async handleTranscription() {
        const formData = new FormData(this.form);
        let url = formData.get('videoUrl');
        const language = formData.get('language');

        if (!url) {
            this.showStatus('Por favor, insira uma URL válida do YouTube.', 'error');
            return;
        }

        // Auto-fix URL format: add https:// if protocol is missing
        if (!url.startsWith('http://') && !url.startsWith('https://')) {
            url = 'https://' + url;
        }

        try {
            this.setLoading(true);
            this.hideResult();
            this.showStatus('Iniciando download do áudio...', 'info');
            this.showProgress();

            const response = await fetch(`${API_BASE_URL}/transcribe`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    url: url,
                    language: language
                })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Erro na requisição');
            }

            this.showStatus('Processando transcrição...', 'info');

            const data = await response.json();

            if (data.success) {
                this.showStatus('Transcrição concluída com sucesso!', 'success');
                this.showResult(data);
            } else {
                throw new Error(data.error || 'Erro desconhecido na transcrição');
            }

        } catch (error) {
            console.error('Erro:', error);
            this.showStatus(`Erro: ${error.message}`, 'error');
            this.hideResult();
        } finally {
            this.setLoading(false);
            this.hideProgress();
        }
    }

    downloadTranscription() {
        const text = this.transcriptionText.value;
        if (!text) return;

        const blob = new Blob([text], { type: 'text/plain;charset=utf-8' });
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        
        const timestamp = new Date().toISOString().slice(0, 19).replace(/:/g, '-');
        link.download = `transcricao_${timestamp}.txt`;
        link.href = url;
        
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);

        this.showStatus('Arquivo baixado com sucesso!', 'success');
        setTimeout(() => this.hideStatus(), 3000);
    }

    async copyTranscription() {
        const text = this.transcriptionText.value;
        if (!text) return;

        try {
            await navigator.clipboard.writeText(text);
            this.showStatus('Texto copiado para a área de transferência!', 'success');
            setTimeout(() => this.hideStatus(), 3000);
        } catch (error) {
            // Fallback for older browsers
            this.transcriptionText.select();
            document.execCommand('copy');
            this.showStatus('Texto copiado para a área de transferência!', 'success');
            setTimeout(() => this.hideStatus(), 3000);
        }
    }

    async handleVideoDownload() {
        const formData = new FormData(this.form);
        let url = formData.get('videoUrl');

        if (!url) {
            this.showStatus('Por favor, insira uma URL válida do YouTube.', 'error');
            return;
        }

        // Auto-fix URL format: add https:// if protocol is missing
        if (!url.startsWith('http://') && !url.startsWith('https://')) {
            url = 'https://' + url;
        }

        try {
            this.setVideoLoading(true);
            this.hideResult();
            this.showStatus('Iniciando download do vídeo...', 'info');
            this.showProgress();

            const response = await fetch(`${API_BASE_URL}/download`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    url: url
                })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Erro na requisição');
            }

            this.showStatus('Processando download...', 'info');

            // Get filename from response headers
            const contentDisposition = response.headers.get('Content-Disposition');
            let filename = 'video.mp4';
            if (contentDisposition) {
                const filenameMatch = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
                if (filenameMatch) {
                    filename = filenameMatch[1].replace(/['"]/g, '');
                }
            }

            // Download file
            const blob = await response.blob();
            const downloadUrl = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            
            link.download = filename;
            link.href = downloadUrl;
            
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            window.URL.revokeObjectURL(downloadUrl);

            this.showStatus('Vídeo baixado com sucesso!', 'success');

        } catch (error) {
            console.error('Erro:', error);
            this.showStatus(`Erro: ${error.message}`, 'error');
        } finally {
            this.setVideoLoading(false);
            this.hideProgress();
        }
    }
}

// Initialize the application when the page loads
document.addEventListener('DOMContentLoaded', () => {
    new TranskiptorUI();
});