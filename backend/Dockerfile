# Use Ubuntu 24.04 with Python 3.12 for newer GLIBC
FROM ubuntu:24.04

# Install Python 3.12 and pip
RUN apt-get update && apt-get install -y \
    python3.12 \
    python3.12-dev \
    python3.12-venv \
    python3-pip \
    && ln -sf /usr/bin/python3.12 /usr/bin/python \
    && ln -sf /usr/bin/python3.12 /usr/bin/python3

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies (Ubuntu 24.04 requires --break-system-packages)
RUN pip install --no-cache-dir -r requirements.txt --break-system-packages

# Copy application code (excluding tools directory first)
COPY . .

# Compile whisper.cpp inside container (Ubuntu 24.04 has newer GLIBC)
RUN if [ ! -f /app/tools/whisper_cpp/main ]; then \
        echo "Compiling whisper.cpp with Ubuntu 24.04..." && \
        cd /tmp && \
        git clone https://github.com/ggml-org/whisper.cpp.git && \
        cd whisper.cpp && \
        make && \
        mkdir -p /app/tools/whisper_cpp && \
        cp build/bin/whisper-cli /app/tools/whisper_cpp/main 2>/dev/null || cp main /app/tools/whisper_cpp/main && \
        cp build/src/libwhisper.so* /app/tools/whisper_cpp/ 2>/dev/null || cp libwhisper.so* /app/tools/whisper_cpp/ 2>/dev/null || true && \
        cp build/ggml/src/libggml*.so* /app/tools/whisper_cpp/ 2>/dev/null || cp libggml*.so* /app/tools/whisper_cpp/ 2>/dev/null || true && \
        chmod +x /app/tools/whisper_cpp/main && \
        echo "Downloading whisper model..." && \
        bash models/download-ggml-model.sh base && \
        cp models/ggml-base.bin /app/tools/whisper_cpp/ && \
        cd / && rm -rf /tmp/whisper.cpp; \
    fi

# Create logs directory
RUN mkdir -p /app/logs

# Expose port
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]