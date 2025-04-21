"""
gemma_image_describe.py

Analyse une image et génère une description en français avec Gemma‑3‑4B‑PT.

Usage (dans le conteneur) :
    python gemma_image_describe.py \
        --prompt "Décris l'image."

Prérequis :
  * Variable d'environnement HF_TOKEN (jeton Hugging Face avec licence Gemma).
  * GPU CUDA compatible (≥ 12 GB VRAM recommandé, ex. RTX 4070 Ti).
"""
import os
from pathlib import Path

import torch
from PIL import Image
from transformers import pipeline

# ID du modèle Hugging Face
MODEL_ID = "google/gemma-3-4b-pt"

# Chemin codé en dur de l'image à analyser
IMAGE_PATH = Path("/app/images/test.jpg")

# Prompt par défaut
DEFAULT_PROMPT = "Décris l'image en détail."


def load_gemma_pipe():
    """Initialise le pipeline Gemma 3 pour vision + texte."""
    return pipeline(
        task="image-text-to-text",
        model=MODEL_ID,
        device=0 if torch.cuda.is_available() else -1,
        torch_dtype=torch.bfloat16 if torch.cuda.is_available() else None,
    )


def build_messages(img: Image.Image, prompt: str):
    """Construit un message au format chat pour Gemma 3."""
    return [
        {
            "role": "user",
            "content": [
                {"type": "image", "image": img},
                {"type": "text", "text": prompt},
            ],
        }
    ]


def main():
    # On utilise le chemin codé en dur
    img_path = IMAGE_PATH
    if not img_path.exists():
        raise FileNotFoundError(f"Image introuvable : {img_path}")

    # Lecture de l'image
    img = Image.open(img_path).convert("RGB")

    # Chargement du pipeline et génération du message
    pipe = load_gemma_pipe()
    messages = build_messages(img, DEFAULT_PROMPT)

    # Génère la description
    output = pipe(text=messages, max_new_tokens=120)
    generated = output[0].get("generated_text", [])
    description = generated[-1]["content"] if generated else ""
    print(description)


if __name__ == "__main__":
    main()

