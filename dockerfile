
#construction de l'image ici nous l'appelerons langchainv2-app
#docker build -t langchainv2-app .
#l'image est maintenant créer, il ne nous manque plus qu'a créer le container qui sera basé sur le fichier docker-compose.yml
# Utiliser une image NVIDIA CUDA compatible
FROM nvidia/cuda:12.1.1-base-ubuntu22.04

# ---------- Paquets système ----------
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        git \
        python3 \
        python3-pip \
        libcudnn8 \
        libcudnn8-dev \
        libgl1 \
    && rm -rf /var/lib/apt/lists/*

# ---------- PyTorch CUDA 12.1 ----------
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
        torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# ---------- Gemma 3 + dépendances vision ----------
RUN pip install --no-cache-dir --upgrade \
        transformers==4.51.3 \
        accelerate \
        pillow \
        einops \
        safetensors \
        xformers

# ---------- Projet ----------
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


CMD [ "bash" ]