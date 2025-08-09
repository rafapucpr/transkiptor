const API_BASE_URL = '/api/v1';

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

        // Audio upload elements
        this.audioForm = document.getElementById('audioTranscriptionForm');
        this.fileUploadArea = document.getElementById('fileUploadArea');
        this.audioFile = document.getElementById('audioFile');
        this.fileInfo = document.getElementById('fileInfo');
        this.fileName = document.getElementById('fileName');
        this.fileSize = document.getElementById('fileSize');
        this.transcribeAudioBtn = document.getElementById('transcribeAudioBtn');
        this.outputFormat = document.getElementById('outputFormat');
        this.audioStatusMessage = document.getElementById('audioStatusMessage');
        this.audioProgressBar = document.getElementById('audioProgressBar');

        // Video upload elements
        this.videoForm = document.getElementById('videoTranscriptionForm');
        this.videoUploadArea = document.getElementById('videoUploadArea');
        this.videoFile = document.getElementById('videoFile');
        this.videoFileInfo = document.getElementById('videoFileInfo');
        this.videoFileName = document.getElementById('videoFileName');
        this.videoFileSize = document.getElementById('videoFileSize');
        this.transcribeVideoBtn = document.getElementById('transcribeVideoBtn');
        this.videoOutputFormat = document.getElementById('videoOutputFormat');
        this.videoStatusMessage = document.getElementById('videoStatusMessage');
        this.videoProgressBar = document.getElementById('videoProgressBar');

        this.selectedFile = null;
        this.selectedVideoFile = null;


        this.initEventListeners();
    }

    initEventListeners() {
        // YouTube transcription events
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

        // Audio upload events
        this.audioForm.addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleAudioTranscription();
        });

        this.fileUploadArea.addEventListener('click', () => {
            this.audioFile.click();
        });

        this.fileUploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            this.fileUploadArea.classList.add('dragover');
        });

        this.fileUploadArea.addEventListener('dragleave', () => {
            this.fileUploadArea.classList.remove('dragover');
        });

        this.fileUploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            this.fileUploadArea.classList.remove('dragover');
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                this.handleFileSelection(files[0]);
            }
        });

        this.audioFile.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                this.handleFileSelection(e.target.files[0]);
            }
        });

        // Video upload events
        this.videoForm.addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleVideoTranscription();
        });

        this.videoUploadArea.addEventListener('click', () => {
            this.videoFile.click();
        });

        this.videoUploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            this.videoUploadArea.classList.add('dragover');
        });

        this.videoUploadArea.addEventListener('dragleave', () => {
            this.videoUploadArea.classList.remove('dragover');
        });

        this.videoUploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            this.videoUploadArea.classList.remove('dragover');
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                this.handleVideoFileSelection(files[0]);
            }
        });

        this.videoFile.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                this.handleVideoFileSelection(e.target.files[0]);
            }
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

            const response = await fetch(`${API_BASE_URL}/transcribe-youtube`, {
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

            const response = await fetch(`${API_BASE_URL}/download-youtube`, {
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

    // Audio upload methods
    showAudioStatus(message, type = 'info') {
        this.audioStatusMessage.textContent = message;
        this.audioStatusMessage.className = `status-message ${type}`;
        this.audioStatusMessage.style.display = 'block';
    }

    hideAudioStatus() {
        this.audioStatusMessage.style.display = 'none';
    }

    showAudioProgress() {
        this.audioProgressBar.style.display = 'block';
    }

    hideAudioProgress() {
        this.audioProgressBar.style.display = 'none';
    }

    setAudioLoading(loading) {
        const btnText = this.transcribeAudioBtn.querySelector('.btn-text');
        const btnLoading = this.transcribeAudioBtn.querySelector('.btn-loading');
        
        if (loading) {
            this.transcribeAudioBtn.disabled = true;
            btnText.style.display = 'none';
            btnLoading.style.display = 'flex';
        } else {
            this.transcribeAudioBtn.disabled = this.selectedFile ? false : true;
            btnText.style.display = 'block';
            btnLoading.style.display = 'none';
        }
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    validateAudioFile(file) {
        const allowedTypes = [
            'audio/wav', 'audio/mp3', 'audio/mpeg', 'audio/m4a', 
            'audio/ogg', 'audio/webm', 'audio/flac', 'audio/x-flac',
            'audio/aac', 'video/mp4', 'video/quicktime', 'video/x-msvideo'
        ];
        
        const allowedExtensions = ['.wav', '.mp3', '.m4a', '.ogg', '.webm', '.flac', '.aac', '.mp4', '.mov', '.avi'];
        const fileExtension = file.name.toLowerCase().substr(file.name.lastIndexOf('.'));
        
        const maxSize = 100 * 1024 * 1024; // 100MB
        
        if (!allowedTypes.includes(file.type) && !allowedExtensions.includes(fileExtension)) {
            return { valid: false, error: 'Formato de arquivo não suportado' };
        }
        
        if (file.size > maxSize) {
            return { valid: false, error: 'Arquivo muito grande (máximo 100MB)' };
        }
        
        return { valid: true };
    }

    handleFileSelection(file) {
        const validation = this.validateAudioFile(file);
        
        if (!validation.valid) {
            this.showAudioStatus(validation.error, 'error');
            return;
        }
        
        this.selectedFile = file;
        
        // Update UI
        this.fileUploadArea.classList.add('file-selected');
        this.fileUploadArea.querySelector('.file-upload-icon').textContent = '✓';
        this.fileUploadArea.querySelector('.file-upload-text').textContent = 'Arquivo selecionado';
        this.fileUploadArea.querySelector('.file-upload-hint').textContent = 'Clique novamente para selecionar outro arquivo';
        
        // Show file info
        this.fileName.textContent = file.name;
        this.fileSize.textContent = this.formatFileSize(file.size);
        this.fileInfo.style.display = 'block';
        
        // Enable transcribe button
        this.transcribeAudioBtn.disabled = false;
        
        this.hideAudioStatus();
    }

    async handleAudioTranscription() {
        if (!this.selectedFile) {
            this.showAudioStatus('Por favor, selecione um arquivo de áudio.', 'error');
            return;
        }

        const language = document.getElementById('audioLanguage').value;
        const outputFormat = this.outputFormat.value;

        try {
            this.setAudioLoading(true);
            this.showAudioStatus('Enviando arquivo...', 'info');
            this.showAudioProgress();

            // Create FormData for file upload
            const formData = new FormData();
            formData.append('file', this.selectedFile);
            formData.append('language', language);
            formData.append('output_format', outputFormat);

            const response = await fetch(`${API_BASE_URL}/transcribe-audio/download`, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Erro na requisição');
            }

            this.showAudioStatus('Transcrição concluída! Baixando arquivo...', 'success');

            // Get filename from response headers
            const contentDisposition = response.headers.get('Content-Disposition');
            let filename = `transcription.${outputFormat}`;
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

            this.showAudioStatus(`Transcrição baixada como ${filename}!`, 'success');
            setTimeout(() => this.hideAudioStatus(), 5000);

        } catch (error) {
            console.error('Erro:', error);
            this.showAudioStatus(`Erro: ${error.message}`, 'error');
        } finally {
            this.setAudioLoading(false);
            this.hideAudioProgress();
        }
    }

    // Video upload methods
    showVideoStatus(message, type = 'info') {
        this.videoStatusMessage.textContent = message;
        this.videoStatusMessage.className = `status-message ${type}`;
        this.videoStatusMessage.style.display = 'block';
    }

    hideVideoStatus() {
        this.videoStatusMessage.style.display = 'none';
    }

    showVideoProgress() {
        this.videoProgressBar.style.display = 'block';
    }

    hideVideoProgress() {
        this.videoProgressBar.style.display = 'none';
    }

    setVideoLoading2(loading) {
        const btnText = this.transcribeVideoBtn.querySelector('.btn-text');
        const btnLoading = this.transcribeVideoBtn.querySelector('.btn-loading');
        
        if (loading) {
            this.transcribeVideoBtn.disabled = true;
            btnText.style.display = 'none';
            btnLoading.style.display = 'flex';
        } else {
            this.transcribeVideoBtn.disabled = this.selectedVideoFile ? false : true;
            btnText.style.display = 'block';
            btnLoading.style.display = 'none';
        }
    }

    validateVideoFile(file) {
        const allowedTypes = [
            'video/mp4', 'video/avi', 'video/mov', 'video/quicktime',
            'video/x-msvideo', 'video/mkv', 'video/webm', 'video/x-flv',
            'video/x-ms-wmv', 'video/3gpp', 'video/ogg'
        ];
        
        const allowedExtensions = ['.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.wmv', '.m4v', '.3gp', '.ogv'];
        const fileExtension = file.name.toLowerCase().substr(file.name.lastIndexOf('.'));
        
        const maxSize = 5 * 1024 * 1024 * 1024; // 5GB
        
        if (!allowedTypes.includes(file.type) && !allowedExtensions.includes(fileExtension)) {
            return { valid: false, error: 'Formato de arquivo não suportado' };
        }
        
        if (file.size > maxSize) {
            return { valid: false, error: 'Arquivo muito grande (máximo 5GB)' };
        }
        
        return { valid: true };
    }

    handleVideoFileSelection(file) {
        const validation = this.validateVideoFile(file);
        
        if (!validation.valid) {
            this.showVideoStatus(validation.error, 'error');
            return;
        }
        
        this.selectedVideoFile = file;
        
        // Update UI
        this.videoUploadArea.classList.add('file-selected');
        this.videoUploadArea.querySelector('.file-upload-icon').textContent = '✓';
        this.videoUploadArea.querySelector('.file-upload-text').textContent = 'Vídeo selecionado';
        this.videoUploadArea.querySelector('.file-upload-hint').textContent = 'Clique novamente para selecionar outro arquivo';
        
        // Show file info
        this.videoFileName.textContent = file.name;
        this.videoFileSize.textContent = this.formatFileSize(file.size);
        this.videoFileInfo.style.display = 'block';
        
        // Enable transcribe button
        this.transcribeVideoBtn.disabled = false;
        
        this.hideVideoStatus();
    }

    async handleVideoTranscription() {
        if (!this.selectedVideoFile) {
            this.showVideoStatus('Por favor, selecione um arquivo de vídeo.', 'error');
            return;
        }

        const language = document.getElementById('videoLanguage').value;
        const outputFormat = this.videoOutputFormat.value;

        try {
            this.setVideoLoading2(true);
            this.showVideoStatus('Enviando arquivo de vídeo...', 'info');
            this.showVideoProgress();

            // Create FormData for file upload
            const formData = new FormData();
            formData.append('file', this.selectedVideoFile);
            formData.append('language', language);
            formData.append('output_format', outputFormat);

            const response = await fetch(`${API_BASE_URL}/transcribe-video/download`, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Erro na requisição');
            }

            this.showVideoStatus('Transcrição concluída! Baixando arquivo...', 'success');

            // Get filename from response headers
            const contentDisposition = response.headers.get('Content-Disposition');
            let filename = `transcription.${outputFormat}`;
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

            this.showVideoStatus(`Transcrição do vídeo baixada como ${filename}!`, 'success');
            setTimeout(() => this.hideVideoStatus(), 5000);

        } catch (error) {
            console.error('Erro:', error);
            this.showVideoStatus(`Erro: ${error.message}`, 'error');
        } finally {
            this.setVideoLoading2(false);
            this.hideVideoProgress();
        }
    }
}

// Initialize the application when the page loads
document.addEventListener('DOMContentLoaded', () => {
    new TranskiptorUI();
});