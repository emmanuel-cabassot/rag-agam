# construction de l'image ici nous l'appelerons langchainv2-app
# docker build -t langchainv2-app .
# l'image est maintenant créer, il ne nous manque plus qu'a créer le container qui sera basé sur le fichier docker-compose.yml
# Utiliser une image NVIDIA CUDA compatible
FROM nvidia/cuda:12.1.1-base-ubuntu22.04  

# Installer Python 3, pip et les dépendances système requises
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    python3 \
    python3-pip \
    libcudnn8 \
    libcudnn8-dev \
    && rm -rf /var/lib/apt/lists/*

# Installer les librairies NVIDIA PyTorch compatibles
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Définir le répertoire de travail dans le conteneur
WORKDIR /app

# Copier et installer les dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

