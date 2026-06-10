# AutoTest-Agent All-in-One Production Dockerfile
# Includes Python + C/C++ + Java runtimes with domestic mirror optimizations

FROM python:3.11-slim

LABEL org.opencontainers.image.title="AutoTest-Agent"
LABEL org.opencontainers.image.description="AI-powered Auto-Test Agent with multi-language runtime"
LABEL org.opencontainers.image.source="https://github.com/MasterDecade/AutoTest-Agent"
LABEL org.opencontainers.image.version="0.1.0"

# ===== Environment =====
ARG PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
ENV PIP_INDEX_URL=${PIP_INDEX_URL}
ENV PIP_NO_CACHE_DIR=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# ===== System Dependencies (domestic mirrors) =====
# Layer 1: Base system + compilers
RUN sed -i 's/deb.debian.org/mirrors.ustc.edu.cn/g' /etc/apt/sources.list.d/debian.sources && \
    sed -i 's/security.debian.org/mirrors.ustc.edu.cn/g' /etc/apt/sources.list.d/debian.sources && \
    apt-get update -o Acquire::http::No-Cache=True && \
    apt-get install -y --no-install-recommends \
        # C/C++ toolchain
        build-essential gcc g++ make cmake \
        # Java toolchain
        openjdk-17-jdk-headless \
        # Static analysis tools
        cppcheck \
        # Database clients
        libpq-dev \
        # Utilities
        curl ca-certificates git \
    && rm -rf /var/lib/apt/lists/*

# ===== Python Dependencies =====
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ===== Python Dev Tools (optional, installed separately) =====
RUN pip install --no-cache-dir pylint pytest coverage

# ===== Application Code =====
COPY . .

# ===== Build frontend (if present) =====
# Node.js is NOT included in this image to keep it slim;
# frontend is served separately or pre-built in CI/CD

# ===== Runtime Directories =====
RUN mkdir -p /data /tmp/autotest

# ===== Healthcheck =====
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/api/health || exit 1

# ===== Expose =====
EXPOSE 8080

# ===== Entrypoint =====
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "2"]